import pytest

pd = pytest.importorskip('pandas')

from backend.services import catalog_data


def test_fetch_customer_catalog_normalizes_fields(monkeypatch):
    df = pd.DataFrame(
        [
            {
                'id': '1',
                'nom': 'Produit',
                'categorie': None,
                'prix_achat': '1,20',
                'prix_vente': None,
                'stock_actuel': None,
                'ventes_30j': None,
                'code': ' 123 456 789 012 ',
            }
        ]
    )

    monkeypatch.setattr(
        catalog_data,
        'query_df',
        lambda *_args, **_kwargs: df.rename(columns={'code': 'ean'}),
    )

    result = catalog_data.fetch_customer_catalog()
    assert result.loc[0, 'categorie'] == 'Autre'
    assert result.loc[0, 'prix_vente'] == 0.0
    assert result.loc[0, 'ean'] == '123456789012'


def test_fetch_recent_suppliers_defaults(monkeypatch):
    df = pd.DataFrame([{'produit_id': 1, 'fournisseur': None, 'date_mvt': '2024-01-01'}])
    monkeypatch.setattr(catalog_data, 'query_df', lambda *_args, **_kwargs: df.copy())

    result = catalog_data.fetch_recent_suppliers()
    assert result.loc[0, 'fournisseur'] == 'Non renseigné'
