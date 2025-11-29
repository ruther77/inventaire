from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from collections import OrderedDict

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from core.data_repository import get_engine, query_df
from core.price_history_service import fetch_latest_price_per_code


def _fetch_tenants() -> pd.DataFrame:
    return query_df("SELECT id, code, name FROM tenants ORDER BY id")


LOGGER = logging.getLogger(__name__)


def _tenant_entities_fallback() -> list[dict[str, object]]:
    tenants = _fetch_tenants()
    return [
        {
            "entity_id": int(row.id),
            "code": row.code,
            "name": row.name,
            "members": [
                {"tenant_id": int(row.id), "code": row.code, "name": row.name},
            ],
        }
        for row in tenants.itertuples()
    ]


def _fetch_entities() -> list[dict[str, object]]:
    try:
        df = query_df(
            text(
                """
                SELECT fe.id AS entity_id,
                       fe.code AS entity_code,
                       fe.name AS entity_name,
                       fem.tenant_id,
                       t.code AS tenant_code,
                       t.name AS tenant_name
                FROM finance_entities fe
                LEFT JOIN finance_entity_members fem ON fem.entity_id = fe.id
                LEFT JOIN tenants t ON t.id = fem.tenant_id
                ORDER BY fe.id, t.id
                """
            )
        )
    except SQLAlchemyError as exc:
        LOGGER.warning("Impossible de charger finance_entities, fallback tenant unique: %s", exc)
        return _tenant_entities_fallback()
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.warning("Erreur inattendue finance_entities: %s", exc)
        return _tenant_entities_fallback()
    if df.empty:
        return _tenant_entities_fallback()
    grouped: OrderedDict[int, dict[str, object]] = OrderedDict()
    for row in df.to_dict("records"):
        entry = grouped.setdefault(
            int(row["entity_id"]),
            {
                "entity_id": int(row["entity_id"]),
                "code": row["entity_code"],
                "name": row["entity_name"],
                "members": [],
            },
        )
        tenant_id = row.get("tenant_id")
        if tenant_id:
            entry["members"].append(
                {"tenant_id": int(tenant_id), "code": row["tenant_code"], "name": row["tenant_name"]}
            )
    return list(grouped.values())


def _latest_price_total(tenant_id: int) -> Decimal:
    df = query_df(
        text(
            """
            SELECT COALESCE(SUM(prix_achat * COALESCE(quantite, 1)), 0) AS stock_value
            FROM latest_price_history
            WHERE tenant_id = :tenant_id
            """
        ),
        params={"tenant_id": int(tenant_id)},
    )
    if df.empty:
        return Decimal("0")
    return Decimal(str(df.iloc[0].stock_value or 0))


def _bank_balance(tenant_id: int) -> Decimal:
    df = query_df(
        text(
            """
            SELECT COALESCE(SUM(
                CASE
                    WHEN LOWER(type) LIKE 'entrée%' THEN montant
                    ELSE -montant
                END
            ), 0) AS balance
            FROM restaurant_bank_statements
            WHERE tenant_id = :tenant_id
            """
        ),
        params={"tenant_id": int(tenant_id)},
    )
    if df.empty:
        return Decimal("0")
    return Decimal(str(df.iloc[0].balance or 0))


def _cash_balance(tenant_id: int) -> Decimal:
    return Decimal("0")


def _tenant_snapshots() -> dict[int, dict[str, object]]:
    tenants_df = _fetch_tenants()
    snapshots: dict[int, dict[str, object]] = {}
    for row in tenants_df.itertuples():
        tenant_id = int(row.id)
        stock_value = _latest_price_total(tenant_id=tenant_id)
        bank_balance = _bank_balance(tenant_id=tenant_id)
        cash_balance = _cash_balance(tenant_id=tenant_id)
        assets = stock_value + bank_balance + cash_balance
        snapshots[tenant_id] = {
            "tenant_id": tenant_id,
            "code": row.code,
            "name": row.name,
            "stock_value": stock_value,
            "bank_balance": bank_balance,
            "cash_balance": cash_balance,
            "total_assets": assets,
            "snapshot_date": datetime.utcnow(),
        }
    return snapshots


def _format_snapshot(snapshot: dict[str, object]) -> dict[str, object]:
    return {
        "tenant_id": snapshot["tenant_id"],
        "code": snapshot["code"],
        "name": snapshot["name"],
        "stock_value": float(snapshot["stock_value"]),
        "bank_balance": float(snapshot["bank_balance"]),
        "cash_balance": float(snapshot["cash_balance"]),
        "total_assets": float(snapshot["total_assets"]),
        "snapshot_date": snapshot.get("snapshot_date"),
    }


def build_capital_overview(limit_latest_prices: int = 20) -> dict[str, object]:
    tenant_snapshots = _tenant_snapshots()
    entities = _fetch_entities()

    entity_entries: list[dict[str, object]] = []
    total_stock = Decimal("0")
    total_bank = Decimal("0")
    total_cash = Decimal("0")
    total_assets = Decimal("0")

    for entity in entities:
        members: list[dict[str, object]] = []
        stock_value = Decimal("0")
        bank_balance = Decimal("0")
        cash_balance = Decimal("0")
        assets = Decimal("0")
        for member in entity.get("members", []):
            snapshot = tenant_snapshots.get(member["tenant_id"])
            if not snapshot:
                continue
            members.append(_format_snapshot(snapshot))
            stock_value += snapshot["stock_value"]
            bank_balance += snapshot["bank_balance"]
            cash_balance += snapshot["cash_balance"]
            assets += snapshot["total_assets"]

        entity_entries.append(
            {
                "entity_id": entity["entity_id"],
                "code": entity["code"],
                "name": entity["name"],
                "stock_value": float(stock_value),
                "bank_balance": float(bank_balance),
                "cash_balance": float(cash_balance),
                "total_assets": float(assets),
                "members": members,
            }
        )
        total_stock += stock_value
        total_bank += bank_balance
        total_cash += cash_balance
        total_assets += assets

    latest_prices_df = fetch_latest_price_per_code(limit=limit_latest_prices)

    return {
        "entities": entity_entries,
        "global": {
            "stock_value": float(total_stock),
            "bank_balance": float(total_bank),
            "cash_balance": float(total_cash),
            "total_assets": float(total_assets),
            "snapshot_date": datetime.utcnow(),
        },
        "latest_prices": latest_prices_df.replace({"": None}).to_dict(orient="records")
        if not latest_prices_df.empty
        else [],
    }


def persist_daily_snapshot(snapshot_date: datetime | None = None) -> None:
    snapshot_date = snapshot_date or datetime.utcnow()
    tenants_df = _fetch_tenants()
    eng = get_engine()
    with eng.begin() as conn:
        for row in tenants_df.itertuples():
            tenant_id = int(row.id)
            stock_value = _latest_price_total(tenant_id=tenant_id)
            bank_balance = _bank_balance(tenant_id=tenant_id)
            cash_balance = _cash_balance(tenant_id=tenant_id)
            total_assets = stock_value + bank_balance + cash_balance
            conn.execute(
                text(
                    """
                    INSERT INTO capital_snapshot (tenant_id, snapshot_date, stock_value, bank_balance, cash_balance, total_assets, created_at)
                    VALUES (:tenant_id, :snapshot_date, :stock_value, :bank_balance, :cash_balance, :total_assets, NOW())
                    ON CONFLICT (tenant_id, snapshot_date)
                    DO UPDATE SET
                        stock_value = EXCLUDED.stock_value,
                        bank_balance = EXCLUDED.bank_balance,
                        cash_balance = EXCLUDED.cash_balance,
                        total_assets = EXCLUDED.total_assets,
                        created_at = NOW()
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "snapshot_date": snapshot_date,
                    "stock_value": float(stock_value),
                    "bank_balance": float(bank_balance),
                    "cash_balance": float(cash_balance),
                    "total_assets": float(total_assets),
                },
            )
