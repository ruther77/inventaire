"""Backfill restaurant -> finance tables (comptes, catégories, fournisseurs, transactions, relevés)."""

from __future__ import annotations

import hashlib
import math
import re
from datetime import date
from typing import Any, Dict, Tuple

from sqlalchemy import text

from core.data_repository import get_engine, query_df


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "code"


def _tenant_to_entity() -> Dict[int, int]:
    df = query_df(
        text(
            """
            SELECT t.id AS tenant_id, fe.id AS entity_id
            FROM tenants t
            JOIN finance_entities fe ON fe.code = t.code
            """
        )
    )
    mapping = {int(row["tenant_id"]): int(row["entity_id"]) for row in df.to_dict("records")}
    # Force tenant_id=3 (tresorerie) à pointer vers l'entité restaurant si disponible pour les flux bancaires.
    if 3 in mapping and 3 in mapping.values():
        mapping[3] = 3
    return mapping


def _ensure_categories(engine, tenant_entity_map: Dict[int, int]) -> Dict[Tuple[int, int], int]:
    mapping: Dict[Tuple[int, int], int] = {}
    src = query_df(text("SELECT id, tenant_id, nom FROM restaurant_depense_categories"))
    if src.empty:
        return mapping
    with engine.begin() as conn:
        for row in src.itertuples():
            entity_id = tenant_entity_map.get(int(row.tenant_id))
            if not entity_id:
                continue
            code = _slugify(row.nom)
            existing = conn.execute(
                text(
                    """
                    SELECT id FROM finance_categories
                    WHERE entity_id IS NOT DISTINCT FROM :entity_id AND code = :code
                    """
                ),
                {"entity_id": entity_id, "code": code},
            ).fetchone()
            if existing:
                mapping[(row.tenant_id, row.id)] = int(existing.id)
                continue
            new_id = conn.execute(
                text(
                    """
                    INSERT INTO finance_categories (entity_id, name, type, parent_id, code)
                    VALUES (:entity_id, :name, 'DEPENSE', NULL, :code)
                    RETURNING id
                    """
                ),
                {"entity_id": entity_id, "name": row.nom, "code": code},
            ).scalar_one()
            mapping[(row.tenant_id, row.id)] = int(new_id)
    return mapping


def _ensure_cost_centers(engine, tenant_entity_map: Dict[int, int]) -> Dict[Tuple[int, int], int]:
    mapping: Dict[Tuple[int, int], int] = {}
    src = query_df(text("SELECT id, tenant_id, nom FROM restaurant_cost_centers"))
    if src.empty:
        return mapping
    with engine.begin() as conn:
        for row in src.itertuples():
            entity_id = tenant_entity_map.get(int(row.tenant_id))
            if not entity_id:
                continue
            code = _slugify(row.nom)
            existing = conn.execute(
                text(
                    """
                    SELECT id FROM finance_cost_centers
                    WHERE entity_id = :entity_id AND code = :code
                    """
                ),
                {"entity_id": entity_id, "code": code},
            ).fetchone()
            if existing:
                mapping[(row.tenant_id, row.id)] = int(existing.id)
                continue
            new_id = conn.execute(
                text(
                    """
                    INSERT INTO finance_cost_centers (entity_id, name, code)
                    VALUES (:entity_id, :name, :code)
                    RETURNING id
                    """
                ),
                {"entity_id": entity_id, "name": row.nom, "code": code},
            ).scalar_one()
            mapping[(row.tenant_id, row.id)] = int(new_id)
    return mapping


def _ensure_vendors(engine, tenant_entity_map: Dict[int, int]) -> Dict[Tuple[int, int], int]:
    mapping: Dict[Tuple[int, int], int] = {}
    src = query_df(text("SELECT id, tenant_id, nom, siret, iban FROM restaurant_fournisseurs"))
    proc = query_df(text("SELECT DISTINCT tenant_id, supplier AS nom FROM processed_invoices WHERE supplier IS NOT NULL"))
    names: set[str] = set()
    if not src.empty:
        names.update(str(row.nom) for row in src.itertuples())
    if not proc.empty:
        names.update(str(row.nom) for row in proc.itertuples())

    all_entity_ids = sorted(set(tenant_entity_map.values()))

    with engine.begin() as conn:
        for name in sorted(names):
            existing = conn.execute(
                text(
                    """
                    SELECT id, entity_id FROM finance_vendors
                    WHERE lower(name) = lower(:name)
                    LIMIT 1
                    """
                ),
                {"name": name},
            ).fetchone()
            for entity_id in all_entity_ids:
                if existing and existing.entity_id == entity_id:
                    continue
                conn.execute(
                    text(
                        """
                        INSERT INTO finance_vendors (entity_id, name, is_active)
                        VALUES (:entity_id, :name, TRUE)
                        ON CONFLICT (entity_id, name) DO NOTHING
                        """
                    ),
                    {"entity_id": entity_id, "name": name},
                )

        for row in src.itertuples():
            for entity_id in all_entity_ids:
                vendor_row = conn.execute(
                    text(
                        """
                        SELECT id FROM finance_vendors
                        WHERE entity_id = :entity_id AND lower(name) = lower(:name)
                        LIMIT 1
                        """
                    ),
                    {"entity_id": entity_id, "name": row.nom},
                ).fetchone()
                if vendor_row:
                    mapping[(row.tenant_id, row.id)] = int(vendor_row.id)
    return mapping


def _deduce_account_type(label: str) -> str:
    low = label.lower()
    if "caisse" in low or "cash" in low:
        return "CAISSE"
    if "cb" in low or "carte" in low or "sumup" in low:
        return "CB"
    return "BANQUE"


def _ensure_accounts(engine, tenant_entity_map: Dict[int, int]) -> Dict[Tuple[int, str], int]:
    mapping: Dict[Tuple[int, str], int] = {}
    src = query_df(
        text(
            """
            SELECT DISTINCT tenant_id, account
            FROM restaurant_bank_statements
            WHERE account IS NOT NULL AND account <> ''
            """
        )
    )
    if src.empty:
        return mapping
    with engine.begin() as conn:
        for row in src.itertuples():
            entity_id = tenant_entity_map.get(int(row.tenant_id))
            if not entity_id:
                continue
            raw_label = row.account
            low_raw = raw_label.lower()
            # Nomenclature normalisée alignée sur les relevés /releve (LCL + SumUp)
            if "noutam" in low_raw:
                label = "LCL - NOUTAM"
            elif "incontournable" in low_raw or "l'incontournable" in low_raw:
                label = "LCL - INCONTOURNABLE"
            elif "sumup" in low_raw:
                label = "SUMUP - INCONTOURNABLE"
            else:
                label = raw_label
            existing = conn.execute(
                text(
                    """
                    SELECT id FROM finance_accounts
                    WHERE entity_id = :entity_id AND label = :label
                    """
                ),
                {"entity_id": entity_id, "label": label},
            ).fetchone()
            if existing:
                mapping[(row.tenant_id, raw_label)] = int(existing.id)
                continue
            acc_type = "PLATFORM" if label == "SUMUP" else _deduce_account_type(label)
            new_id = conn.execute(
                text(
                    """
                    INSERT INTO finance_accounts (entity_id, type, label, currency, is_active)
                    VALUES (:entity_id, :type, :label, 'EUR', TRUE)
                    RETURNING id
                    """
                ),
                {"entity_id": entity_id, "type": acc_type, "label": label},
            ).scalar_one()
            mapping[(row.tenant_id, raw_label)] = int(new_id)
    return mapping


def _month_bounds(day: date) -> tuple[date, date]:
    start = day.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1) - start.resolution
    else:
        end = start.replace(month=start.month + 1, day=1) - start.resolution
    return start, end


def _backfill_bank_statements(engine, tenant_entity_map, account_map) -> None:
    rows = query_df(
        text(
            """
            SELECT id, tenant_id, account, date, libelle, montant, type, source
            FROM restaurant_bank_statements
            ORDER BY date, id
            """
        )
    )
    if rows.empty:
        return
    statement_cache: Dict[tuple[int, int, int], int] = {}
    with engine.begin() as conn:
        for row in rows.itertuples():
            entity_id = tenant_entity_map.get(int(row.tenant_id))
            account_id = account_map.get((row.tenant_id, row.account))
            if not entity_id or not account_id:
                continue
            month_key = (account_id, row.date.year, row.date.month)
            statement_id = statement_cache.get(month_key)
            if not statement_id:
                period_start, period_end = _month_bounds(row.date)
                existing_stmt = conn.execute(
                    text(
                        """
                        SELECT id FROM finance_bank_statements
                        WHERE account_id = :account_id AND period_start = :period_start
                        LIMIT 1
                        """
                    ),
                    {"account_id": account_id, "period_start": period_start},
                ).fetchone()
                if existing_stmt:
                    statement_id = int(existing_stmt.id)
                else:
                    statement_id = conn.execute(
                        text(
                            """
                            INSERT INTO finance_bank_statements (account_id, period_start, period_end, source)
                            VALUES (:account_id, :period_start, :period_end, :source)
                            RETURNING id
                            """
                        ),
                        {
                            "account_id": account_id,
                            "period_start": period_start,
                            "period_end": period_end,
                            "source": row.source or "IMPORT",
                        },
                    ).scalar_one()
                statement_cache[month_key] = int(statement_id)

            signed_amount = float(row.montant or 0)
            if row.type and str(row.type).lower().startswith("sortie"):
                signed_amount = -abs(signed_amount)
            checksum = hashlib.sha1(f"{row.date}|{signed_amount}|{row.libelle}".encode("utf-8")).hexdigest()
            exists = conn.execute(
                text(
                    """
                    SELECT 1 FROM finance_bank_statement_lines
                    WHERE statement_id = :statement_id AND checksum = :checksum
                    """
                ),
                {"statement_id": statement_id, "checksum": checksum},
            ).fetchone()
            if exists:
                continue
            conn.execute(
                text(
                    """
                    INSERT INTO finance_bank_statement_lines (
                        statement_id,
                        date_operation,
                        date_valeur,
                        libelle_banque,
                        montant,
                        balance_apres,
                        ref_banque,
                        raw_data,
                        checksum
                    ) VALUES (
                        :statement_id,
                        :date_operation,
                        :date_valeur,
                        :libelle_banque,
                        :montant,
                        NULL,
                        :ref_banque,
                        NULL,
                        :checksum
                    )
                    """
                ),
                {
                    "statement_id": statement_id,
                    "date_operation": row.date,
                    "date_valeur": row.date,
                    "libelle_banque": row.libelle,
                    "montant": signed_amount,
                    "ref_banque": row.id,
                    "checksum": checksum,
                },
            )


def _backfill_transactions(engine, tenant_entity_map, category_map, cost_center_map, vendor_map, account_map) -> None:
    rows = query_df(
        text(
            """
            SELECT
                d.id,
                d.tenant_id,
                d.categorie_id,
                d.fournisseur_id,
                d.cost_center_id,
                d.libelle,
                d.montant_ht,
                d.tva_pct,
                d.date_operation,
                d.source,
                d.ref_externe
            FROM restaurant_depenses d
            ORDER BY d.date_operation, d.id
            """
        )
    )
    if rows.empty:
        return

    statement_account_map: Dict[int, str] = {}
    st_rows = query_df(text("SELECT depense_id, account FROM restaurant_bank_statements WHERE depense_id IS NOT NULL"))
    for r in st_rows.itertuples():
        if r.depense_id and r.account:
            statement_account_map[int(r.depense_id)] = r.account

    with engine.begin() as conn:
        for row in rows.itertuples():
            entity_id = tenant_entity_map.get(int(row.tenant_id))
            if not entity_id:
                continue
            category_id = category_map.get((row.tenant_id, row.categorie_id))
            cost_center_id = cost_center_map.get((row.tenant_id, row.cost_center_id))
            vendor_id = vendor_map.get((row.tenant_id, row.fournisseur_id))

            account_label = statement_account_map.get(int(row.id))
            account_id = account_map.get((row.tenant_id, account_label)) if account_label else None
            if not account_id:
                acc = conn.execute(
                    text(
                        """
                        SELECT id FROM finance_accounts
                        WHERE entity_id = :entity_id
                        ORDER BY id
                        LIMIT 1
                        """
                    ),
                    {"entity_id": entity_id},
                ).fetchone()
                if not acc:
                    continue
                account_id = int(acc.id)

            montant_ht = float(row.montant_ht or 0)
            tva_pct = float(row.tva_pct or 0)
            montant_ttc = montant_ht * (1 + tva_pct / 100) if row.montant_ht is not None else 0.0
            if math.isclose(montant_ttc, 0, abs_tol=1e-6):
                continue

            if row.ref_externe:
                existing = conn.execute(
                    text("SELECT id FROM finance_transactions WHERE ref_externe = :ref_externe"),
                    {"ref_externe": row.ref_externe},
                ).fetchone()
                if existing:
                    continue

            tx_id = conn.execute(
                text(
                    """
                    INSERT INTO finance_transactions (
                        entity_id,
                        account_id,
                        counterparty_account_id,
                        direction,
                        source,
                        date_operation,
                        date_value,
                        amount,
                        currency,
                        ref_externe,
                        note,
                        status
                    ) VALUES (
                        :entity_id,
                        :account_id,
                        NULL,
                        'OUT',
                        :source,
                        :date_operation,
                        :date_operation,
                        :amount,
                        'EUR',
                        :ref_externe,
                        :note,
                        'CONFIRMED'
                    )
                    RETURNING id
                    """
                ),
                {
                    "entity_id": entity_id,
                    "account_id": account_id,
                    "source": row.source or "MANUEL",
                    "date_operation": row.date_operation,
                    "amount": montant_ttc,
                    "ref_externe": row.ref_externe,
                    "note": row.libelle,
                },
            ).scalar_one()

            conn.execute(
                text(
                    """
                    INSERT INTO finance_transaction_lines (
                        transaction_id,
                        category_id,
                        cost_center_id,
                        montant_ht,
                        tva_pct,
                        montant_ttc,
                        description,
                        position
                    ) VALUES (
                        :transaction_id,
                        :category_id,
                        :cost_center_id,
                        :montant_ht,
                        :tva_pct,
                        :montant_ttc,
                        :description,
                        1
                    )
                    """
                ),
                {
                    "transaction_id": tx_id,
                    "category_id": category_id,
                    "cost_center_id": cost_center_id,
                    "montant_ht": row.montant_ht,
                    "tva_pct": row.tva_pct,
                    "montant_ttc": montant_ttc,
                    "description": row.libelle,
                },
            )


def run_backfill() -> None:
    engine = get_engine()
    tenant_entity_map = _tenant_to_entity()
    category_map = _ensure_categories(engine, tenant_entity_map)
    cost_center_map = _ensure_cost_centers(engine, tenant_entity_map)
    vendor_map = _ensure_vendors(engine, tenant_entity_map)
    account_map = _ensure_accounts(engine, tenant_entity_map)
    _backfill_bank_statements(engine, tenant_entity_map, account_map)
    _backfill_transactions(engine, tenant_entity_map, category_map, cost_center_map, vendor_map, account_map)
