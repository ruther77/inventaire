import os
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text

fastapi = pytest.importorskip("fastapi", reason="fastapi non installé (pip install fastapi starlette httpx)")
TestClient = pytest.importorskip(
    "fastapi.testclient", reason="fastapi.testclient non disponible"
).TestClient

# Évite toute connexion Postgres lors de l'import des modules backend/core.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SKIP_TENANT_INIT", "1")
os.environ.setdefault("SKIP_USER_INIT", "1")
os.environ.setdefault("APP_ENV", "test")

from backend import main
from backend.dependencies import tenant as tenant_dep
from backend.dependencies import security as security_dep
from core import data_repository


@pytest.fixture()
def sqlite_engine(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=__import__("sqlalchemy.pool", fromlist=["StaticPool"]).StaticPool,
    )
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prix_vente REAL,
                prix_achat REAL,
                stock_actuel REAL,
                actif BOOLEAN DEFAULT 1,
                tenant_id INTEGER NOT NULL
            )
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE mouvements_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produit_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                quantite REAL NOT NULL,
                date_mvt TIMESTAMP NOT NULL,
                tenant_id INTEGER NOT NULL
            )
            """
        )

    # Patch le moteur et la config pool pour toute la stack core.*
    monkeypatch.setattr(data_repository, "get_engine", lambda: engine)
    monkeypatch.setenv("DB_POOL_SIZE", "1")
    monkeypatch.setenv("DB_POOL_MAX_OVERFLOW", "0")
    return engine


def _seed_sample_data(engine):
    now = datetime.now(timezone.utc)
    past = now - timedelta(days=10)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO produits (nom, prix_vente, prix_achat, stock_actuel, actif, tenant_id) "
                "VALUES (:n, :pv, :pa, :s, 1, :t)"
            ),
            [
                {"n": "Produit T1", "pv": 10, "pa": 5, "s": 3, "t": 1},
                {"n": "Produit T2", "pv": 20, "pa": 12, "s": 2, "t": 1},
                {"n": "Autre tenant", "pv": 50, "pa": 30, "s": 9, "t": 2},
            ],
        )
        conn.execute(
            text(
                "INSERT INTO mouvements_stock (produit_id, type, quantite, date_mvt, tenant_id) "
                "VALUES (:pid, :type, :qty, :date, :tenant)"
            ),
            [
                {"pid": 1, "type": "ENTREE", "qty": 5, "date": past, "tenant": 1},
                {"pid": 1, "type": "SORTIE", "qty": 2, "date": now, "tenant": 1},
                {"pid": 2, "type": "SORTIE", "qty": 1, "date": now, "tenant": 1},
                {"pid": 3, "type": "ENTREE", "qty": 99, "date": now, "tenant": 2},
            ],
        )


def test_analytics_summary_isolated_by_tenant(sqlite_engine, monkeypatch):
    _seed_sample_data(sqlite_engine)
    monkeypatch.setenv("SKIP_TENANT_INIT", "1")

    app = main.create_app()

    # Force un utilisateur/tenant de test pour les dépendances
    app.dependency_overrides[security_dep.get_current_user] = lambda: security_dep.AuthenticatedUser(
        id=1, username="tester", role="manager", tenant_id=1
    )
    app.dependency_overrides[tenant_dep.get_current_tenant] = lambda: tenant_dep.Tenant(
        id=1, code="epicerie", name="Épicerie HQ"
    )

    client = TestClient(app)

    resp = client.get("/analytics/summary")
    assert resp.status_code == 200
    data = resp.json()

    # Stock et mouvements ne doivent considérer que le tenant 1
    assert data["products_active"] == 2
    # 10*3 + 20*2 = 70
    assert pytest.approx(data["stock_value_sale"], rel=1e-3) == 70.0
    # 5*3 + 12*2 = 39
    assert pytest.approx(data["stock_value_purchase"], rel=1e-3) == 39.0

    movements = {entry["type"]: entry for entry in data["movements_last_30d"]}
    assert movements["ENTREE"]["count"] == 1
    assert movements["SORTIE"]["count"] == 2
    # Ventes sur 30j : qty=3 (2+1), revenue = 2*10 + 1*20 = 40, cost = 2*5 + 1*12 = 22
    assert pytest.approx(data["sales_qty_30d"], rel=1e-3) == 3.0
    assert pytest.approx(data["sales_revenue_30d"], rel=1e-3) == 40.0
    assert pytest.approx(data["sales_margin_30d"], rel=1e-3) == 18.0
    # Top produits : P2 en tête sur revenue, puis P1
    assert data["top_products_30d"][0]["id"] == 2
    assert pytest.approx(data["top_products_30d"][0]["revenue"], rel=1e-3) == 20.0
    # Top catégories : Non classé (P1/P2) regroupe les ventes
    assert data["top_categories_30d"][0]["categorie"] == "Non classé"
    assert pytest.approx(data["top_categories_30d"][0]["revenue"], rel=1e-3) == 40.0
