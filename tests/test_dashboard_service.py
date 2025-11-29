import pytest

pd = pytest.importorskip('pandas')

from backend.services import dashboard
from tests import sample_data


def test_fetch_kpis_and_lists(monkeypatch):
    kpi_df = pd.DataFrame(
        [
            {
                'total_produits': 4,
                'valeur_stock_ht': 320.0,
                'quantite_stock_total': 52,
                'alerte_stock_bas': 1,
                'stock_epuise': 2,
            }
        ]
    )
    monkeypatch.setattr(dashboard, 'query_df', lambda sql, params=None: kpi_df.copy())

    result = dashboard.fetch_kpis(tenant_id=1)
    assert result['total_produits'] == 4
    assert result['alerte_stock_bas'] == 1


def test_fetch_top_stock_and_sales(monkeypatch):
    def fake_query(sql, params=None):
        if 'FROM v_stock_produits' in sql:
            return sample_data.make_dashboard_stock_df()
        if 'FROM mouvements_stock' in sql:
            return pd.DataFrame(
                [
                    {'nom': 'Produit valeur', 'quantite_vendue': 12},
                    {'nom': 'Produit valeur 2', 'quantite_vendue': 3},
                ]
            )
        if 'FROM produits' in sql:
            return pd.DataFrame(
                [
                    {'statut_stock': 'Épuisé', 'nombre': 2},
                    {'statut_stock': 'Stock OK', 'nombre': 5},
                ]
            )
        return pd.DataFrame()

    monkeypatch.setattr(dashboard, 'query_df', fake_query)

    stock = dashboard.fetch_top_stock_value(tenant_id=1, limit=2)
    assert stock[0]['valeur_stock'] >= stock[1]['valeur_stock']

    sales = dashboard.fetch_top_sales(tenant_id=1, limit=2)
    assert sales[0]['quantite_vendue'] == 12

    status = dashboard.fetch_status_distribution(tenant_id=1)
    assert status[0]['statut_stock'] == 'Épuisé'


def test_fetch_dashboard_metrics_combines_sections(monkeypatch):
    monkeypatch.setattr(dashboard, 'fetch_kpis', lambda tenant_id: {'total_produits': 1})
    monkeypatch.setattr(dashboard, 'fetch_top_stock_value', lambda tenant_id: [{'nom': 'X', 'valeur_stock': 10}])
    monkeypatch.setattr(dashboard, 'fetch_top_sales', lambda tenant_id: [{'nom': 'X', 'quantite_vendue': 2}])
    monkeypatch.setattr(dashboard, 'fetch_status_distribution', lambda tenant_id: [{'statut_stock': 'OK', 'nombre': 1}])
    monkeypatch.setattr(dashboard, 'fetch_supplier_breakdown', lambda tenant_id: [])
    monkeypatch.setattr(dashboard, 'fetch_weekly_variation', lambda tenant_id: [])
    monkeypatch.setattr(dashboard, 'fetch_margin_alerts', lambda tenant_id: [])

    result = dashboard.fetch_dashboard_metrics(tenant_id=1)

    assert result['kpis']['total_produits'] == 1
    assert result['top_stock_value'][0]['nom'] == 'X'
