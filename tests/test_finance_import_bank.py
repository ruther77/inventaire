from datetime import date

from backend.services.importers import bank_statement_csv


def test_parse_csv_basic():
    content = """date;libelle;montant;ref
2024-12-01;Paiement CB;-12,34;ABC
01/12/2024;Virement;+100.00;DEF
"""
    rows = bank_statement_csv.parse_csv(content.replace(";", ","))
    assert len(rows) == 2
    assert rows[0]["date_operation"] == date(2024, 12, 1)
    assert abs(rows[0]["montant"] - -12.34) < 1e-6
    assert rows[0]["ref_banque"] == "ABC"
    assert rows[1]["date_operation"] == date(2024, 12, 1)
    assert abs(rows[1]["montant"] - 100.0) < 1e-6
    assert rows[1]["ref_banque"] == "DEF"
