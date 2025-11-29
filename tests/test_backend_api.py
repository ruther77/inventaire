import os
import pytest

os.environ.setdefault('SKIP_TENANT_INIT', '1')
os.environ.setdefault('SKIP_USER_BOOTSTRAP', '1')

if not os.environ.get('RUN_BACKEND_API_TESTS'):
    pytest.skip('Tests API désactivés (RUN_BACKEND_API_TESTS non défini).', allow_module_level=True)

import pandas as pd  # noqa: WPS433 - dépendance nécessaire uniquement si les tests sont activés

pytest.importorskip('fastapi')

from fastapi.testclient import TestClient

from backend.main import app
from backend.dependencies.security import create_access_token
from backend.dependencies.tenant import Tenant


@pytest.fixture(autouse=True)
def disable_invoice_tracking(monkeypatch):
    monkeypatch.setattr(
        'backend.api.invoices.invoices_service.find_processed_invoice_ids',
        lambda *_args, **_kwargs: set(),
    )
    monkeypatch.setattr(
        'backend.api.invoices.invoices_service.record_processed_invoices',
        lambda *_args, **_kwargs: None,
    )


def _make_token(role: str = 'admin', tenant_id: int = 1) -> str:
    return create_access_token(
        {
            'sub': '1',
            'username': 'test-user',
            'role': role,
            'tenant_id': tenant_id,
        }
    )


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {'Authorization': f'Bearer {_make_token()}'}


@pytest.fixture
def api_client(auth_headers):
    client = TestClient(app)
    client.headers.update(auth_headers)
    return client


@pytest.fixture(autouse=True)
def mock_tenant_resolution(monkeypatch):
    monkeypatch.setattr(
        'backend.dependencies.tenant.resolve_tenant',
        lambda *_args, **_kwargs: Tenant(id=1, code='epicerie', name='Épicerie HQ'),
    )


def test_health_endpoint(api_client):
    response = api_client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_products_listing(api_client, monkeypatch):
    client = api_client

    monkeypatch.setattr('backend.main._fetch_products', lambda: [])

    response = client.get('/products')
    assert response.status_code == 200
    assert response.json() == []


def test_checkout_success(api_client, monkeypatch):
    client = api_client

    def fake_checkout(cart, username, tenant_id):
        assert cart == [{'id': 1, 'nom': 'Test', 'prix_vente': 2.5, 'tva': 5.5, 'qty': 1}]
        assert username == 'api_user'
        assert tenant_id == 1
        return True, None, {'filename': 'ticket.pdf', 'content': b'binary'}

    monkeypatch.setattr('backend.main.process_sale_transaction', fake_checkout)

    response = client.post(
        '/pos/checkout',
        json={'cart': [{'id': 1, 'nom': 'Test', 'prix_vente': 2.5, 'tva': 5.5, 'qty': 1}], 'username': None},
    )
    assert response.status_code == 200
    body = response.json()
    assert body['success'] is True
    assert body['receipt_filename'] == 'ticket.pdf'
    assert body['receipt_base64'] is not None


def test_product_update(api_client, monkeypatch):
    client = api_client
    called = {}

    def fake_update(product_id, changes, barcodes):
        called['product_id'] = product_id
        called['changes'] = changes
        called['barcodes'] = barcodes
        return {'fields_updated': len(changes)}

    monkeypatch.setattr('backend.main.update_catalog_entry', fake_update)

    response = client.patch(
        '/products/123',
        json={'nom': 'Nouveau nom', 'barcodes': ['1234567890123', '  ']},
    )

    assert response.status_code == 200
    assert called == {
        'product_id': 123,
        'changes': {'nom': 'Nouveau nom'},
        'barcodes': ['1234567890123'],
    }
    assert response.json()['status'] == 'updated'


def test_supply_plan_endpoint(api_client, monkeypatch):
    client = api_client
    captured = {}
    fake_payload = {
        'params': {
            'target_coverage': 30,
            'alert_threshold': 10,
            'min_daily_sales': 1.0,
            'categories': ['Boissons'],
            'search': None,
        },
        'summary': {
            'analyzed': 0,
            'recommended_count': 0,
            'units_to_order': 0,
            'value_total': 0.0,
            'margin_total': 0.0,
        },
        'available_categories': ['Boissons', 'Epicerie'],
        'items': [],
        'supplier_breakdown': [],
    }

    def fake_compute(**kwargs):
        captured.update(kwargs)
        return fake_payload

    monkeypatch.setattr('backend.api.supply.supply_service.compute_supply_plan', fake_compute)

    response = client.get('/supply/plan?target_coverage=30&alert_threshold=10&min_daily_sales=1&categories=Boissons')
    assert response.status_code == 200
    assert captured['target_coverage'] == 30
    assert captured['alert_threshold'] == 10
    assert captured['min_daily_sales'] == 1
    assert captured['categories'] == ['Boissons']
    body = response.json()
    assert body == fake_payload


def test_audit_diagnostics_endpoint(api_client, monkeypatch):
    client = api_client
    payload = {
        'available_categories': ['Boissons'],
        'summary': {'anomalies': 1, 'delta': 1.0, 'assigned': 0, 'open_tasks': 0},
        'items': [
            {
                'product_id': 1,
                'nom': 'Produit A',
                'categorie': 'Boissons',
                'stock_actuel': 10.0,
                'stock_calcule': 8.0,
                'ecart': 2.0,
                'ecart_abs': 2.0,
                'niveau_ecart': 'Modéré',
                'responsable': None,
                'action_status': None,
                'action_id': None,
            }
        ],
    }

    def fake_diag(**kwargs):
        return payload

    monkeypatch.setattr('backend.api.audit.audit_service.list_diagnostics', fake_diag)

    resp = client.get('/audit/diagnostics')
    assert resp.status_code == 200
    assert resp.json() == payload


def test_audit_assignment_endpoint(api_client, monkeypatch):
    client = api_client
    created = {
        'id': 1,
        'product_id': 42,
        'responsable': 'Alice',
        'note': 'Vérifier',
        'status': 'À compter',
        'due_date': None,
        'created_at': '2024-01-01T00:00:00',
    }
    monkeypatch.setattr('backend.api.audit.audit_service.create_assignment', lambda **kwargs: created)

    resp = client.post(
        '/audit/assignments',
        json={
            'product_id': 42,
            'responsable': 'Alice',
            'note': 'Vérifier',
            'due_date': None,
            'create_task': True,
        },
    )
    assert resp.status_code == 201
    assert resp.json() == created


def test_invoice_extract_endpoint(api_client, monkeypatch):
    client = api_client
    sample_df = pd.DataFrame(
        [
            {
                'nom': 'Produit X',
                'codes': '1234567890123',
                'prix_achat': 10.0,
                'prix_vente': 15.0,
                'tva': 5.5,
                'qte_init': 1,
                'quantite_recue': 1,
                'invoice_id': 'INV-001',
                'facture_date': '2024-01-01',
            }
        ]
    )

    monkeypatch.setattr(
        'backend.api.invoices.invoices_service.extract_invoice_lines',
        lambda text, margin_percent: sample_df,
    )
    monkeypatch.setattr(
        'backend.api.invoices.invoices_service.enrich_lines_with_catalog',
        lambda df, margin_percent, tenant_id: df,
    )

    resp = client.post('/invoices/extract', json={'text': 'facture brute', 'margin_percent': 30})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body['items']) == 1
    assert body['items'][0]['nom'] == 'Produit X'
    assert body['documents'][0]['invoice_id'] == 'INV-001'
    assert body['documents'][0]['line_count'] == 1


def test_invoice_import_endpoint(api_client, monkeypatch):
    client = api_client
    summary = {
        'rows_received': 1,
        'movements_created': 1,
        'quantity_total': 12.0,
        'errors': [],
    }

    def fake_apply(df, username, supplier, movement_type, invoice_date, tenant_id):
        assert len(df) == 1
        assert supplier == 'Metro'
        assert invoice_date == '2024-01-10'
        assert tenant_id == 1
        return summary

    monkeypatch.setattr('backend.api.invoices.invoices_service.apply_invoice_import', fake_apply)

    resp = client.post(
        '/invoices/import',
        json={
            'lines': [
                {
                    'nom': 'Produit Y',
                    'codes': '321',
                    'prix_achat': 12.0,
                    'prix_vente': 18.0,
                    'tva': 5.5,
                    'qte_init': 6,
                    'quantite_recue': 6,
                    'produit_id': 1,
                    'invoice_id': 'INV-XYZ',
                }
            ],
            'supplier': 'Metro',
            'movement_type': 'ENTREE',
            'username': 'api',
            'invoice_date': '2024-01-10',
        },
    )
    assert resp.status_code == 200
    assert resp.json() == summary


def test_invoice_catalog_import_endpoint(api_client, monkeypatch):
    client = api_client
    captured = {}
    summary = {'rows_received': 1, 'rows_processed': 1, 'created': 1, 'updated': 0, 'stock_initialized': 0, 'errors': []}

    def fake_catalog(df, supplier, initialize_stock, tenant_id):
        captured['initialize_stock'] = initialize_stock
        captured['supplier'] = supplier
        return summary

    monkeypatch.setattr('backend.api.invoices.invoices_service.import_catalog_from_invoice', fake_catalog)

    resp = client.post(
        '/invoices/catalog/import',
        json={
            'lines': [
                {'nom': 'Produit Z', 'prix_achat': 2.0, 'prix_vente': 4.0, 'tva': 5.5, 'invoice_id': 'INV-CAT'}
            ],
            'supplier': 'Metro',
            'username': 'api',
            'initialize_stock': True,
        },
    )
    assert resp.status_code == 200
    assert resp.json() == summary


def test_invoice_history_endpoint(api_client, monkeypatch):
    client = api_client
    sample_rows = [
        {
            'invoice_id': 'INV-001',
            'supplier': 'Metro',
            'facture_date': '2024-01-01',
            'line_count': 10,
            'file_path': '/tmp/invoice.pdf',
            'created_at': '2024-01-05T00:00:00',
            'updated_at': '2024-01-05T00:00:00',
        }
    ]

    monkeypatch.setattr(
        'backend.api.invoices.invoices_service.list_processed_invoices',
        lambda **kwargs: sample_rows,
    )

    resp = client.get('/invoices/history?supplier=Metro')
    assert resp.status_code == 200
    body = resp.json()
    assert len(body['items']) == 1
    assert body['items'][0]['invoice_id'] == 'INV-001'
    assert captured == {'initialize_stock': True, 'supplier': 'Metro'}


def test_stock_adjustment_endpoint(api_client, monkeypatch):
    client = api_client
    expected = {
        'product_id': 1,
        'product_name': 'Produit A',
        'current_stock': 5.0,
        'new_stock': 7.0,
        'movement_created': True,
        'movement_type': 'ENTREE',
        'movement_quantity': 2.0,
    }

    monkeypatch.setattr('backend.api.stock.stock_service.adjust_stock_level', lambda *args, **kwargs: expected)

    resp = client.post('/stock/adjustments', json={'product_id': 1, 'target_quantity': 7})
    assert resp.status_code == 200
    assert resp.json() == expected


def test_dashboard_metrics_endpoint(api_client, monkeypatch):
    client = api_client
    payload = {
        'kpis': {
            'total_produits': 10,
            'valeur_stock_ht': 1000.0,
            'quantite_stock_total': 200.0,
            'alerte_stock_bas': 2,
            'stock_epuise': 1,
        },
        'top_stock_value': [{'nom': 'Produit A', 'valeur_stock': 500.0}],
        'top_sales': [{'nom': 'Produit B', 'quantite_vendue': 30.0}],
        'status_distribution': [{'statut_stock': 'Stock OK', 'nombre': 5}],
    }

    monkeypatch.setattr(
        'backend.api.dashboard.dashboard_service.fetch_dashboard_metrics',
        lambda *, tenant_id: payload,
    )

    resp = client.get('/dashboard/metrics')
    assert resp.status_code == 200
    assert resp.json() == payload


def test_supply_plan_endpoint(api_client, monkeypatch):
    client = api_client
    captured = {}
    expected = {'items': [], 'summary': {'analyzed': 0}, 'params': {}}

    def fake_compute(**kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr('backend.api.supply.supply_service.compute_supply_plan', fake_compute)

    resp = client.get('/supply/plan?target_coverage=30&alert_threshold=5&min_daily_sales=1.5&categories=Boissons&search=eau')
    assert resp.status_code == 200
    assert resp.json() == expected
    assert captured['target_coverage'] == 30
    assert captured['categories'] == ['Boissons']
    assert captured['search'] == 'eau'


def test_supply_plan_endpoint_error(api_client, monkeypatch):
    client = api_client

    def boom(**_):
        raise RuntimeError('db down')

    monkeypatch.setattr('backend.api.supply.supply_service.compute_supply_plan', boom)

    resp = client.get('/supply/plan')
    assert resp.status_code == 500
    assert resp.json()['detail'] == 'db down'


def test_audit_diagnostics_endpoint(api_client, monkeypatch):
    client = api_client
    captured = {}
    expected = {'items': [{'product_id': 1}], 'summary': {'anomalies': 1}}

    def fake_list(**kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr('backend.api.audit.audit_service.list_diagnostics', fake_list)

    resp = client.get('/audit/diagnostics?categories=Boissons&levels=Critique&min_abs=2&max_abs=10')
    assert resp.status_code == 200
    assert resp.json() == expected
    assert captured['categories'] == ['Boissons']
    assert captured['levels'] == ['Critique']
    assert captured['min_abs'] == 2.0
    assert captured['max_abs'] == 10.0


def test_create_audit_assignment_validation(api_client, monkeypatch):
    client = api_client

    def fake_create(**kwargs):
        raise ValueError('Produit inconnu')

    monkeypatch.setattr('backend.api.audit.audit_service.create_assignment', fake_create)

    resp = client.post(
        '/audit/assignments',
        json={'product_id': 99, 'responsable': 'Alice', 'note': 'test', 'due_date': None, 'create_task': True},
    )
    assert resp.status_code == 400
    assert resp.json()['detail'] == 'Produit inconnu'
