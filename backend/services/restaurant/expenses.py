"""Services de gestion des dépenses pour le module restaurant."""

from __future__ import annotations

from typing import Any, List

from sqlalchemy import text

from core.data_repository import get_engine, query_df
from backend.services.restaurant.utils import _safe_float


def list_depense_categories(tenant_id: int) -> List[dict[str, Any]]:
    """Liste toutes les catégories de dépense pour un tenant."""
    df = query_df(
        text(
            """
            SELECT id, nom
            FROM restaurant_depense_categories
            WHERE tenant_id = :tenant
            ORDER BY nom
            """
        ),
        {"tenant": tenant_id},
    )
    return df.to_dict("records") if not df.empty else []


def create_depense_category(tenant_id: int, nom: str) -> dict[str, Any]:
    """Crée une nouvelle catégorie de dépense."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_depense_categories (tenant_id, nom)
                VALUES (:tenant, :nom)
                RETURNING id, nom
                """
            ),
            {"tenant": tenant_id, "nom": nom},
        ).fetchone()
    return dict(row._mapping)


def list_cost_centers(tenant_id: int) -> List[dict[str, Any]]:
    """Liste tous les centres de coûts pour un tenant."""
    df = query_df(
        text(
            """
            SELECT id, nom
            FROM restaurant_cost_centers
            WHERE tenant_id = :tenant
            ORDER BY nom
            """
        ),
        {"tenant": tenant_id},
    )
    return df.to_dict("records") if not df.empty else []


def create_cost_center(tenant_id: int, nom: str) -> dict[str, Any]:
    """Crée un nouveau centre de coûts."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_cost_centers (tenant_id, nom)
                VALUES (:tenant, :nom)
                RETURNING id, nom
                """
            ),
            {"tenant": tenant_id, "nom": nom},
        ).fetchone()
    return dict(row._mapping)


def list_fournisseurs(tenant_id: int) -> List[dict[str, Any]]:
    """Liste tous les fournisseurs pour un tenant."""
    df = query_df(
        text(
            """
            SELECT id, nom
            FROM restaurant_fournisseurs
            WHERE tenant_id = :tenant
            ORDER BY nom
            """
        ),
        {"tenant": tenant_id},
    )
    return df.to_dict("records") if not df.empty else []


def create_fournisseur(tenant_id: int, nom: str) -> dict[str, Any]:
    """Crée un nouveau fournisseur."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_fournisseurs (tenant_id, nom)
                VALUES (:tenant, :nom)
                RETURNING id, nom
                """
            ),
            {"tenant": tenant_id, "nom": nom},
        ).fetchone()
    return dict(row._mapping)


def list_expenses(tenant_id: int) -> List[dict[str, Any]]:
    """Liste toutes les dépenses d'un tenant avec données enrichies."""
    sql = """
        SELECT d.id,
               d.libelle,
               d.date_operation,
               COALESCE(dc.nom, '') AS categorie,
               COALESCE(cc.nom, '') AS cost_center,
               COALESCE(f.nom, '') AS fournisseur,
               COALESCE(d.montant_ht, d.quantite * d.prix_unitaire) AS montant_ht,
               COALESCE(d.montant_ht, d.quantite * d.prix_unitaire) * (1 + COALESCE(d.tva_pct,0)/100.0) AS montant_ttc
        FROM restaurant_depenses d
        LEFT JOIN restaurant_depense_categories dc ON dc.id = d.categorie_id
        LEFT JOIN restaurant_cost_centers cc ON cc.id = d.cost_center_id
        LEFT JOIN restaurant_fournisseurs f ON f.id = d.fournisseur_id
        WHERE d.tenant_id = :tenant
        ORDER BY d.date_operation DESC, d.id DESC
    """
    df = query_df(text(sql), {"tenant": tenant_id})
    return df.to_dict("records") if not df.empty else []


def get_expense_detail(tenant_id: int, expense_id: int) -> dict[str, Any] | None:
    """Récupère le détail d'une dépense donnée."""
    sql = """
        SELECT d.id,
               d.libelle,
               d.date_operation,
               COALESCE(dc.nom, '') AS categorie,
               COALESCE(cc.nom, '') AS cost_center,
               COALESCE(f.nom, '') AS fournisseur,
               COALESCE(d.montant_ht, d.quantite * d.prix_unitaire) AS montant_ht,
               COALESCE(d.montant_ht, d.quantite * d.prix_unitaire) * (1 + COALESCE(d.tva_pct,0)/100.0) AS montant_ttc
        FROM restaurant_depenses d
        LEFT JOIN restaurant_depense_categories dc ON dc.id = d.categorie_id
        LEFT JOIN restaurant_cost_centers cc ON cc.id = d.cost_center_id
        LEFT JOIN restaurant_fournisseurs f ON f.id = d.fournisseur_id
        WHERE d.tenant_id = :tenant AND d.id = :id
        LIMIT 1
    """
    df = query_df(text(sql), {"tenant": tenant_id, "id": expense_id})
    if df.empty:
        return None
    return df.to_dict("records")[0]


def create_expense(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Insère une dépense et renvoie l'enregistrement enrichi."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_depenses (
                    tenant_id, categorie_id, cost_center_id, fournisseur_id,
                    libelle, unite, quantite, prix_unitaire, montant_ht, tva_pct,
                    date_operation, source, ref_externe
                ) VALUES (
                    :tenant_id, :categorie_id, :cost_center_id, :fournisseur_id,
                    :libelle, :unite, :quantite, :prix_unitaire, :montant_ht, :tva_pct,
                    :date_operation, :source, :ref_externe
                )
                RETURNING id
                """
            ),
            payload,
        ).fetchone()
    expense = get_expense_detail(tenant_id, row.id)
    if not expense:
        raise RuntimeError("Impossible de recuperer la depense creee")
    return expense


def expense_summary_by_month(tenant_id: int, months: int = 6) -> List[dict[str, Any]]:
    """Agrège les dépenses par mois sur la période demandée."""
    sql = """
        SELECT TO_CHAR(DATE_TRUNC('month', date_operation), 'YYYY-MM') AS label,
               SUM(COALESCE(montant_ht, quantite * prix_unitaire)) AS total_ht
        FROM restaurant_depenses
        WHERE tenant_id = :tenant
          AND date_operation >= (CURRENT_DATE - INTERVAL ':months months')
        GROUP BY 1
        ORDER BY 1 DESC
    """
    df = query_df(text(sql.replace(':months', str(max(1, months)))), {"tenant": tenant_id})
    return df.to_dict("records") if not df.empty else []


def expense_summary_by_cost_center(tenant_id: int, months: int = 3) -> List[dict[str, Any]]:
    """Répartit les dépenses par centre de coûts sur la période récente."""
    window = max(1, months)
    sql = """
        SELECT
            COALESCE(NULLIF(cc.nom, ''), 'Non affecte') AS label,
            SUM(COALESCE(d.montant_ht, d.quantite * d.prix_unitaire)) AS total_ht
        FROM restaurant_depenses d
        LEFT JOIN restaurant_cost_centers cc ON cc.id = d.cost_center_id
        WHERE d.tenant_id = :tenant
          AND d.date_operation >= (CURRENT_DATE - INTERVAL ':window months')
        GROUP BY label
        ORDER BY total_ht DESC NULLS LAST
        """
    clause = text(sql.replace(":window", str(window)))
    df = query_df(clause, {"tenant": tenant_id})
    return df.to_dict("records") if not df.empty else []


def expense_summary_by_tva(tenant_id: int, months: int = 6) -> List[dict[str, Any]]:
    """Résume les montants HT/TVA/TTC pour la déclaration fiscale."""
    window = max(1, months)
    sql = """
        SELECT
            DATE_TRUNC('month', d.date_operation)::date AS periode,
            COALESCE(d.tva_pct, 0) AS taux,
            SUM(COALESCE(d.montant_ht, d.quantite * d.prix_unitaire)) AS montant_ht,
            SUM(COALESCE(d.montant_ht, d.quantite * d.prix_unitaire) * COALESCE(d.tva_pct, 0) / 100.0) AS montant_tva
        FROM restaurant_depenses d
        WHERE d.tenant_id = :tenant
          AND d.date_operation >= (CURRENT_DATE - INTERVAL ':window months')
        GROUP BY periode, taux
        ORDER BY periode ASC, taux ASC
    """
    clause = text(sql.replace(":window", str(window)))
    df = query_df(clause, {"tenant": tenant_id})
    if df.empty:
        return []
    df["montant_ht"] = df["montant_ht"].fillna(0.0)
    df["montant_tva"] = df["montant_tva"].fillna(0.0)
    df["montant_ttc"] = df["montant_ht"] + df["montant_tva"]
    return df.to_dict("records")
