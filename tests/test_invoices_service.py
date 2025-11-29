import importlib.util
import os
from datetime import datetime

import pytest

os.environ.setdefault('SKIP_USER_BOOTSTRAP', '1')
os.environ.setdefault('SKIP_TENANT_INIT', '1')

PANDAS_AVAILABLE = importlib.util.find_spec('pandas') is not None
SQLA_AVAILABLE = importlib.util.find_spec('sqlalchemy') is not None
DEPENDENCIES_AVAILABLE = PANDAS_AVAILABLE and SQLA_AVAILABLE

pytestmark = pytest.mark.skipif(
    not DEPENDENCIES_AVAILABLE,
    reason='pandas ou SQLAlchemy non installés',
)

if DEPENDENCIES_AVAILABLE:  # pragma: no cover - guarded import for optional deps
    import pandas as pd
    from backend.services import invoices as invoices_service
else:  # pragma: no cover - tests skipped when deps absent
    pd = None
    invoices_service = None


@pytest.fixture(autouse=True)
def disable_invoice_tracking(monkeypatch):
    if invoices_service is None:
        return
    monkeypatch.setattr(invoices_service, 'record_processed_invoices', lambda *args, **kwargs: None)


def test_apply_invoice_import_auto_matches_products(monkeypatch):
    captured = {}

    def fake_match(_df, tenant_id=1):
        return pd.DataFrame(
            {
                'code': ['1234567890123'],
                'produit_id': [42],
                'produit_nom': ['Produit auto'],
                'categorie': ['Epicerie'],
                'prix_achat_catalogue': [5.0],
                'prix_vente_catalogue': [8.0],
                'tva_catalogue': [5.5],
            }
        )

    def fake_register(df, username, supplier, movement_type, tenant_id, reception_date=None):
        captured['df'] = df.copy()
        return {
            'rows_received': len(df),
            'movements_created': len(df),
            'quantity_total': float(df['quantite_recue'].sum()) if 'quantite_recue' in df else 0.0,
            'errors': [],
        }

    monkeypatch.setattr(invoices_service, 'match_invoice_products', fake_match)
    monkeypatch.setattr(invoices_service, 'register_invoice_reception', fake_register)

    invoice_df = pd.DataFrame(
        [
            {
                'nom': 'Produit auto',
                'codes': '1234567890123',
                'qte_init': 6,
                'quantite_recue': None,
                'produit_id': None,
            }
        ]
    )

    summary = invoices_service.apply_invoice_import(
        invoice_df,
        username='api',
        supplier='Metro',
        invoice_date=datetime(2024, 1, 5),
    )

    assert summary['movements_created'] == 1
    prepared_df = captured['df']
    assert prepared_df['produit_id'].iloc[0] == 42
    assert float(prepared_df['quantite_recue'].iloc[0]) == 6.0


def test_apply_invoice_import_fills_missing_quantities(monkeypatch):
    captured = {}

    def fake_register(df, username, supplier, movement_type, tenant_id, reception_date=None):
        captured['quantities'] = df['quantite_recue'].tolist()
        return {
            'rows_received': len(df),
            'movements_created': len(df),
            'quantity_total': float(df['quantite_recue'].sum()),
            'errors': [],
        }

    monkeypatch.setattr(invoices_service, 'register_invoice_reception', fake_register)

    invoice_df = pd.DataFrame(
        [
            {
                'nom': 'Produit connu',
                'produit_id': 7,
                'qte_init': 3,
            }
        ]
    )

    invoices_service.apply_invoice_import(
        invoice_df,
        username='api',
        supplier='Metro',
        invoice_date=datetime(2024, 1, 6),
    )

    assert captured['quantities'] == [3]
