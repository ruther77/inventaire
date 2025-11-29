from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

import pytest

from backend.services import catalog as catalog_service


@dataclass
class DummyRow:
    _mapping: dict[str, Any]


class DummyCursor:
    def __init__(self, fetchone=None, fetchall=None):
        self._fetchone = fetchone
        self._fetchall = fetchall

    def fetchone(self):
        return self._fetchone

    def fetchall(self):
        return self._fetchall


class DummyConnection:
    def __init__(self, responses):
        self.responses = deque(responses)

    def execute(self, *args, **kwargs):
        try:
            return self.responses.popleft()
        except IndexError:
            raise RuntimeError('No response prepared for execute')


class DummyEngine:
    def __init__(self, conn):
        self._conn = conn

    def begin(self):
        class Ctx:
            def __enter__(inner_self):
                return self._conn

            def __exit__(inner_self, exc_type, exc_val, exc_tb):
                return False

        return Ctx()


def _patch_engine(monkeypatch, conn):
    monkeypatch.setattr('backend.services.catalog.get_engine', lambda: DummyEngine(conn))


def test_list_products_page_filters_and_meta(monkeypatch):
    total_count = 10
    count_cursor = DummyCursor(fetchone=(total_count,))
    row_data = DummyRow(
        _mapping={
            'id': 1,
            'nom': 'Produit A',
            'tenant_id': 1,
            'prix_achat': 5,
            'prix_vente': 10,
            'tva': 20,
            'categorie': 'Boissons',
            'seuil_alerte': 10,
            'stock_actuel': 2,
            'actif': True,
        }
    )
    list_cursor = DummyCursor(fetchall=[row_data])
    conn = DummyConnection([count_cursor, list_cursor])
    monkeypatch.setattr(catalog_service, '_fetch_barcodes', lambda *_args, **_kwargs: ['123'])
    _patch_engine(monkeypatch, conn)

    items, total = catalog_service.list_products_page(
        tenant_id=1,
        search='Produit',
        category='Boissons',
        status='warning',
        page=1,
        per_page=10,
    )

    assert total == total_count
    assert len(items) == 1
    assert items[0]['nom'] == 'Produit A'
    assert items[0]['status'] == 'warning'


def test_list_products_page_status_default(monkeypatch):
    count_cursor = DummyCursor(fetchone=(1,))
    row_data = DummyRow(
        _mapping={
            'id': 2,
            'nom': 'Produit B',
            'tenant_id': 1,
            'prix_achat': 1,
            'prix_vente': 3,
            'tva': 5.5,
            'categorie': 'Boissons',
            'seuil_alerte': 0,
            'stock_actuel': 5,
            'actif': True,
        }
    )
    list_cursor = DummyCursor(fetchall=[row_data])
    conn = DummyConnection([count_cursor, list_cursor])
    monkeypatch.setattr(catalog_service, '_fetch_barcodes', lambda *_args, **_kwargs: [])
    _patch_engine(monkeypatch, conn)

    items, total = catalog_service.list_products_page(
        tenant_id=1,
        status='ok',
        page=1,
        per_page=5,
    )

    assert total == 1
    assert items[0]['status'] == 'ok'
