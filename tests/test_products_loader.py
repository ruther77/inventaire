import sys
import types
from pathlib import Path

import pandas as pd
from sqlalchemy import exc as sa_exc

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core import products_loader  # noqa: E402


class DummyRow:
    def __init__(self, produit_id):
        self.produit_id = produit_id


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyConnection:
    def __init__(self):
        self.executed = []
        self.barcode_map = {}
        self.product_data = {}
        self.product_by_name = {}
        self.next_generic_id = 400

    def execute(self, statement, params=None):
        sql = str(statement)
        self.executed.append((sql, params))
        params = params or {}
        nom = params.get("nom")

        if "SELECT produit_id" in sql and "produits_barcodes" in sql:
            code = (params.get("code") or "").lower()
            if code in self.barcode_map:
                return DummyResult(DummyRow(self.barcode_map[code]))
            return DummyResult(None)
        
        if "SELECT id, prix_achat, prix_vente, categorie" in sql and "FROM produits" in sql:
            if "WHERE id = :pid" in sql:
                pid = int(params.get("pid")) if params.get("pid") is not None else None
                data = self.product_data.get(pid)
                if not data:
                    return DummyResult(None)
                return DummyResult(types.SimpleNamespace(**data))
            if "WHERE lower(nom) = lower(:nom)" in sql:
                key = (params.get("nom") or "").lower()
                pid = self.product_by_name.get(key)
                if pid is None:
                    return DummyResult(None)
                data = self.product_data.get(pid, {"id": pid, "prix_achat": None, "prix_vente": None, "categorie": None})
                return DummyResult(types.SimpleNamespace(**data))
            return DummyResult(None)

        if "UPDATE produits" in sql:
            pid = params.get("pid")
            if pid is not None:
                pid_int = int(pid)
                existing = self.product_data.setdefault(
                    pid_int,
                    {"id": pid_int, "prix_achat": None, "prix_vente": None, "categorie": None},
                )
                if "prix_achat" in params:
                    existing["prix_achat"] = params.get("prix_achat")
                if "prix_vente" in params:
                    existing["prix_vente"] = params.get("prix_vente")
                if "categorie" in params:
                    existing["categorie"] = params.get("categorie")
            if nom:
                key = nom.lower()
                if pid is not None:
                    self.product_by_name[key] = int(pid)
            return DummyResult(None)

        if "INSERT INTO produits (" in sql:
            if nom == "Bière artisanale":
                new_id = 101
            else:
                new_id = self.next_generic_id
                self.next_generic_id += 1

            self.product_data[new_id] = {
                "id": new_id,
                "prix_achat": params.get("prix_achat"),
                "prix_vente": params.get("prix_vente"),
                "categorie": params.get("categorie"),
            }
            if nom:
                self.product_by_name[nom.lower()] = new_id
            return DummyResult(types.SimpleNamespace(id=new_id))

        if "INSERT INTO mouvements_stock" in sql:
            return DummyResult(None)

        if "INSERT INTO produits_barcodes" in sql:
            code = (params.get("code") or "").lower()
            self.barcode_map[code] = params.get("pid")
            return DummyResult(None)

        raise AssertionError(f"Unexpected SQL executed: {sql}")


class DummyContextManager:
    def __init__(self, connection):
        self._connection = connection

    def __enter__(self):
        return self._connection

    def __exit__(self, exc_type, exc, tb):
        return False


class DummyEngine:
    def __init__(self, connection):
        self._connection = connection

    def begin(self):
        return DummyContextManager(self._connection)


def test_insert_or_update_barcode_status_transitions():
    connection = DummyConnection()

    status = products_loader.insert_or_update_barcode(connection, 1, "ABC")
    assert status == "added"

    status = products_loader.insert_or_update_barcode(connection, 1, "abc")
    assert status == "skipped"

    status = products_loader.insert_or_update_barcode(connection, 2, "ABC")
    assert status == "conflict"


def test_clean_codes_and_determine_categorie():
    assert products_loader._clean_codes("111; 222,333\n444") == ["111", "222", "333", "444"]
    assert products_loader._clean_codes(["555", " 666"]) == ["555", "666"]
    assert products_loader.determine_categorie("bière artisanale") == "Alcool"
    assert products_loader.determine_categorie("Savon douceur") == "Hygiene"
    assert products_loader.determine_categorie("Plat Afrique") == "Afrique"


def test_to_float_handles_currency_and_percent():
    assert products_loader._to_float("5,00 EUR") == 5.0
    assert products_loader._to_float("20.00%") == 20.0
    assert products_loader._to_float("   12 % ") == 12.0


def test_load_products_from_df_summarises_results(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "nom": "Bière artisanale",
                "prix_vente": "5,50",
                "tva": "20",
                "prix_achat": "3",
                "qte_init": "4",
                "codes": "111;222",
            },
            {
                "nom": "Savon douceur",
                "prix_vente": "2.0",
                "tva": "5.5",
                "prix_achat": "1.0",
                "codes": "333",
            },
        ]
    )

    connection = DummyConnection()
    connection.product_data[202] = {"id": 202, "prix_achat": 1.2, "prix_vente": 2.5, "categorie": "Hygiene"}
    connection.product_by_name["savon douceur"] = 202
    engine = DummyEngine(connection)
    monkeypatch.setattr(products_loader, "get_engine", lambda: engine)

    barcode_calls = []

    def fake_insert_barcode(conn, produit_id, code):
        barcode_calls.append((produit_id, code))
        if code == "111":
            return "added"
        if code == "222":
            return "skipped"
        if code == "333":
            return "conflict"
        return "skipped"

    monkeypatch.setattr(products_loader, "insert_or_update_barcode", fake_insert_barcode)

    summary = products_loader.load_products_from_df(df)

    assert summary["rows_received"] == 2
    assert summary["rows_processed"] == 2
    assert summary["created"] == 1
    assert summary["updated"] == 1
    assert summary["stock_initialized"] == 1
    assert summary["errors"] == []
    assert summary["barcode"] == {"added": 1, "conflicts": 1, "skipped": 1}
    assert barcode_calls == [(101, "111"), (101, "222"), (202, "333")]


def test_load_products_from_df_updates_existing_with_barcode(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "nom": "Produit existant",
                "prix_vente": "12.50",
                "tva": "20",
                "prix_achat": "8.00",
                "qte_init": "5",
                "codes": "444",
            }
        ]
    )

    connection = DummyConnection()
    connection.barcode_map["444"] = 303
    connection.product_data[303] = {"id": 303, "prix_achat": 7.5, "prix_vente": 10.0, "categorie": "Boissons"}
    engine = DummyEngine(connection)
    monkeypatch.setattr(products_loader, "get_engine", lambda: engine)

    summary = products_loader.load_products_from_df(df)

    assert summary["rows_received"] == 1
    assert summary["rows_processed"] == 1
    assert summary["created"] == 0
    assert summary["updated"] == 1
    assert summary["stock_initialized"] == 1
    assert summary["barcode"] == {"added": 0, "conflicts": 0, "skipped": 1}

    # Vérifie qu'aucune insertion n'a été réalisée et qu'une mise à jour par ID a eu lieu.
    executed_sql = [sql for sql, _ in connection.executed]
    assert not any("INSERT INTO produits (" in sql for sql in executed_sql)
    assert any("WHERE id = :pid" in sql for sql in executed_sql)
    
    update_params = next(params for sql, params in connection.executed if "UPDATE produits" in sql)
    assert update_params["categorie"] == "Boissons"
    
    movement_params = next(
        params for sql, params in connection.executed if "INSERT INTO mouvements_stock" in sql
    )
    assert movement_params["produit_id"] == 303
    assert movement_params["quantite"] == 5.0
    assert movement_params["source"].startswith("Import facture")


def test_load_products_updates_price_on_small_increase(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "nom": "Produit stable",
                "prix_vente": "16.20",
                "tva": "20",
                "prix_achat": "10.50",
                "codes": "555",
            }
        ]
    )

    connection = DummyConnection()
    connection.barcode_map["555"] = 909
    connection.product_data[909] = {"id": 909, "prix_achat": 10.0, "prix_vente": 16.0, "categorie": "Général"}
    engine = DummyEngine(connection)
    monkeypatch.setattr(products_loader, "get_engine", lambda: engine)

    summary = products_loader.load_products_from_df(df)

    assert summary["updated"] == 1
    update_params = next(params for sql, params in connection.executed if "UPDATE produits" in sql)
    assert update_params["prix_achat"] == 10.5
    assert update_params["prix_vente"] == 16.2


def test_load_products_ignores_minor_price_drop(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "nom": "Produit stable",
                "prix_vente": "15.80",
                "tva": "20",
                "prix_achat": "9.60",
                "codes": "555",
            }
        ]
    )

    connection = DummyConnection()
    connection.barcode_map["555"] = 909
    connection.product_data[909] = {"id": 909, "prix_achat": 10.0, "prix_vente": 16.0, "categorie": "Général"}
    engine = DummyEngine(connection)
    monkeypatch.setattr(products_loader, "get_engine", lambda: engine)

    summary = products_loader.load_products_from_df(df)

    assert summary["updated"] == 1
    update_params = next(params for sql, params in connection.executed if "UPDATE produits" in sql)
    # La légère baisse de prix d'achat est ignorée, le prix de vente reste inchangé.
    assert update_params["prix_achat"] == 10.0
    assert update_params["prix_vente"] == 16.0

def test_load_products_from_df_counts_conflict_on_integrity_error(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "nom": "Produit X",
                "prix_vente": "4",
                "tva": "20",
                "prix_achat": "2",
                "codes": "999",
            }
        ]
    )

    connection = DummyConnection()
    engine = DummyEngine(connection)
    monkeypatch.setattr(products_loader, "get_engine", lambda: engine)

    def raise_integrity(conn, produit_id, code):
        raise sa_exc.IntegrityError("stmt", "params", "orig")

    monkeypatch.setattr(products_loader, "insert_or_update_barcode", raise_integrity)

    summary = products_loader.load_products_from_df(df)

    assert summary["barcode"]["conflicts"] == 1
def test_load_products_from_df_records_errors(monkeypatch):
    df = pd.DataFrame([
        {"nom": " ", "prix_vente": "", "tva": ""},
    ])

    connection = DummyConnection()
    engine = DummyEngine(connection)
    monkeypatch.setattr(products_loader, "get_engine", lambda: engine)

    summary = products_loader.load_products_from_df(df)

    assert summary["rows_received"] == 1
    assert summary["rows_processed"] == 1
    assert len(summary["errors"]) == 1
    error = summary["errors"][0]
    assert error["ligne"] == 2
    assert "Nom du produit manquant" in error["erreur"]
    assert len(summary["rejected_rows"]) == 1
    assert "nom" in (summary["rejected_csv"] or "")


def test_process_products_file_missing_file(tmp_path):
    missing = tmp_path / "missing.csv"
    summary = products_loader.process_products_file(str(missing))

    assert summary["rows_received"] == 0
    assert summary["errors"]
    assert "Fichier introuvable" in summary["errors"][0]["erreur"]


def test_load_products_from_df_can_skip_stock_initialization(monkeypatch):
    df = pd.DataFrame(
        [
            {"nom": "Produit sans stock", "prix_vente": "2", "tva": "20", "prix_achat": "1", "qte_init": "5"},
        ]
    )
    connection = DummyConnection()
    engine = DummyEngine(connection)
    monkeypatch.setattr(products_loader, "get_engine", lambda: engine)

    called = []

    def fake_initial_stock(conn, produit_id, quantite, source, tenant_id):
        called.append((produit_id, quantite, source, tenant_id))
        return True

    monkeypatch.setattr(products_loader, "create_initial_stock", fake_initial_stock)

    summary = products_loader.load_products_from_df(df, initialize_stock=False)

    assert called == []
    assert summary["stock_initialized"] == 0


def test_load_products_from_df_initializes_stock_when_requested(monkeypatch):
    df = pd.DataFrame(
        [
            {"nom": "Produit avec stock", "prix_vente": "2", "tva": "20", "prix_achat": "1", "qte_init": "3"},
        ]
    )
    connection = DummyConnection()
    engine = DummyEngine(connection)
    monkeypatch.setattr(products_loader, "get_engine", lambda: engine)

    def fake_initial_stock(conn, produit_id, quantite, source, tenant_id):
        return True

    monkeypatch.setattr(products_loader, "create_initial_stock", fake_initial_stock)

    summary = products_loader.load_products_from_df(df, initialize_stock=True)

    assert summary["stock_initialized"] == 1
