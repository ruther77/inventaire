"""
Inventory snapshot service for daily stock value tracking and period comparisons.

This module provides functionality to:
- Create daily snapshots of inventory values by category
- Compare snapshots between different dates
- Track inventory value evolution over time
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from core.data_repository import get_engine, query_df

LOGGER = logging.getLogger(__name__)


def _calculate_inventory_value(tenant_id: int) -> dict[str, Any]:
    """
    Calculate current inventory value grouped by category.

    Args:
        tenant_id: The tenant ID to calculate inventory for

    Returns:
        Dictionary with total value and category breakdown
    """
    try:
        # Calculate total stock value from current stock levels and prices
        df = query_df(
            text("""
                SELECT
                    COALESCE(p.categorie, 'Non classifié') AS categorie,
                    COUNT(p.id) AS product_count,
                    SUM(p.stock_actuel) AS total_quantity,
                    SUM(p.stock_actuel * COALESCE(p.prix_achat, 0)) AS total_value
                FROM produits p
                WHERE p.tenant_id = :tenant_id
                  AND p.actif = TRUE
                  AND p.stock_actuel > 0
                GROUP BY COALESCE(p.categorie, 'Non classifié')
                ORDER BY total_value DESC
            """),
            params={"tenant_id": int(tenant_id)},
        )

        if df.empty:
            return {
                "total_value": Decimal("0"),
                "total_quantity": Decimal("0"),
                "product_count": 0,
                "categories": [],
            }

        categories = []
        for _, row in df.iterrows():
            categories.append({
                "categorie": row["categorie"],
                "product_count": int(row["product_count"]),
                "total_quantity": float(row["total_quantity"] or 0),
                "total_value": float(row["total_value"] or 0),
            })

        total_value = Decimal(str(df["total_value"].sum() or 0))
        total_quantity = Decimal(str(df["total_quantity"].sum() or 0))
        product_count = int(df["product_count"].sum() or 0)

        return {
            "total_value": total_value,
            "total_quantity": total_quantity,
            "product_count": product_count,
            "categories": categories,
        }

    except SQLAlchemyError as exc:
        LOGGER.error(f"Database error calculating inventory value for tenant {tenant_id}: {exc}")
        return {
            "total_value": Decimal("0"),
            "total_quantity": Decimal("0"),
            "product_count": 0,
            "categories": [],
        }


def create_daily_snapshot(
    tenant_id: int,
    snapshot_date: date | None = None,
) -> dict[str, Any]:
    """
    Create a snapshot of current inventory values.

    This function:
    1. Calculates total stock value from current inventory
    2. Groups values by category
    3. Stores the snapshot in capital_snapshot table

    Args:
        tenant_id: The tenant ID
        snapshot_date: Optional specific date for the snapshot (defaults to today)

    Returns:
        Dictionary with snapshot data including:
        - snapshot_id: The database ID of the created snapshot
        - snapshot_date: The date of the snapshot
        - stock_value: Total inventory value
        - total_assets: Same as stock_value (for compatibility)
        - categories: List of category breakdowns

    Raises:
        SQLAlchemyError: If database operation fails
    """
    if snapshot_date is None:
        snapshot_date = date.today()

    # Convert date to datetime with timezone
    if isinstance(snapshot_date, date) and not isinstance(snapshot_date, datetime):
        snapshot_dt = datetime.combine(snapshot_date, datetime.min.time(), tzinfo=timezone.utc)
    elif isinstance(snapshot_date, datetime):
        snapshot_dt = snapshot_date if snapshot_date.tzinfo else snapshot_date.replace(tzinfo=timezone.utc)
    else:
        snapshot_dt = datetime.now(timezone.utc)

    # Calculate inventory value
    inventory_data = _calculate_inventory_value(tenant_id)
    stock_value = inventory_data["total_value"]

    # For now, bank and cash balances are 0 (inventory snapshot only)
    # These could be integrated with finance module later
    bank_balance = Decimal("0")
    cash_balance = Decimal("0")
    total_assets = stock_value + bank_balance + cash_balance

    eng = get_engine()

    try:
        with eng.begin() as conn:
            # Insert or update snapshot
            result = conn.execute(
                text("""
                    INSERT INTO capital_snapshot
                    (tenant_id, snapshot_date, stock_value, bank_balance, cash_balance, total_assets, created_at)
                    VALUES (:tenant_id, :snapshot_date, :stock_value, :bank_balance, :cash_balance, :total_assets, NOW())
                    ON CONFLICT (tenant_id, snapshot_date)
                    DO UPDATE SET
                        stock_value = EXCLUDED.stock_value,
                        bank_balance = EXCLUDED.bank_balance,
                        cash_balance = EXCLUDED.cash_balance,
                        total_assets = EXCLUDED.total_assets,
                        created_at = NOW()
                    RETURNING id
                """),
                {
                    "tenant_id": int(tenant_id),
                    "snapshot_date": snapshot_dt,
                    "stock_value": float(stock_value),
                    "bank_balance": float(bank_balance),
                    "cash_balance": float(cash_balance),
                    "total_assets": float(total_assets),
                },
            )

            snapshot_id = result.scalar()

            LOGGER.info(
                f"Created inventory snapshot {snapshot_id} for tenant {tenant_id} "
                f"on {snapshot_date}: {stock_value:.2f} EUR"
            )

            return {
                "snapshot_id": snapshot_id,
                "snapshot_date": snapshot_dt.isoformat(),
                "stock_value": float(stock_value),
                "bank_balance": float(bank_balance),
                "cash_balance": float(cash_balance),
                "total_assets": float(total_assets),
                "product_count": inventory_data["product_count"],
                "total_quantity": float(inventory_data["total_quantity"]),
                "categories": inventory_data["categories"],
            }

    except SQLAlchemyError as exc:
        LOGGER.error(f"Failed to create snapshot for tenant {tenant_id}: {exc}")
        raise


def get_snapshot_comparison(
    tenant_id: int,
    date1: date,
    date2: date,
) -> dict[str, Any]:
    """
    Compare two inventory snapshots.

    Args:
        tenant_id: The tenant ID
        date1: First comparison date (typically the earlier date)
        date2: Second comparison date (typically the later date)

    Returns:
        Dictionary with comparison data:
        - date1: First date
        - date2: Second date
        - snapshot1: Data from first snapshot
        - snapshot2: Data from second snapshot
        - difference: Absolute difference in stock value
        - difference_pct: Percentage change
        - evolution: 'increase', 'decrease', or 'stable'

    Raises:
        ValueError: If snapshots don't exist for given dates
    """
    # Convert dates to datetime for query
    if isinstance(date1, date) and not isinstance(date1, datetime):
        dt1 = datetime.combine(date1, datetime.min.time(), tzinfo=timezone.utc)
    else:
        dt1 = date1

    if isinstance(date2, date) and not isinstance(date2, datetime):
        dt2 = datetime.combine(date2, datetime.min.time(), tzinfo=timezone.utc)
    else:
        dt2 = date2

    try:
        # Fetch both snapshots
        df = query_df(
            text("""
                SELECT
                    id,
                    snapshot_date,
                    stock_value,
                    bank_balance,
                    cash_balance,
                    total_assets
                FROM capital_snapshot
                WHERE tenant_id = :tenant_id
                  AND snapshot_date::date IN (:date1, :date2)
                ORDER BY snapshot_date
            """),
            params={
                "tenant_id": int(tenant_id),
                "date1": date1,
                "date2": date2,
            },
        )

        if df.empty:
            raise ValueError(
                f"No snapshots found for tenant {tenant_id} on dates {date1} and {date2}. "
                "Please create snapshots first."
            )

        if len(df) < 2:
            available_date = df.iloc[0]["snapshot_date"].date()
            missing_date = date1 if available_date == date2 else date2
            raise ValueError(
                f"Snapshot found for {available_date} but missing for {missing_date}. "
                "Please create snapshot for the missing date."
            )

        # Extract snapshot data
        snap1 = df.iloc[0].to_dict()
        snap2 = df.iloc[1].to_dict()

        # Calculate differences
        value1 = Decimal(str(snap1["stock_value"] or 0))
        value2 = Decimal(str(snap2["stock_value"] or 0))

        difference = value2 - value1
        difference_pct = (
            (difference / value1 * 100) if value1 != 0 else Decimal("0")
        )

        if difference > 0:
            evolution = "increase"
        elif difference < 0:
            evolution = "decrease"
        else:
            evolution = "stable"

        return {
            "date1": snap1["snapshot_date"].isoformat(),
            "date2": snap2["snapshot_date"].isoformat(),
            "snapshot1": {
                "id": int(snap1["id"]),
                "date": snap1["snapshot_date"].isoformat(),
                "stock_value": float(snap1["stock_value"]),
                "bank_balance": float(snap1["bank_balance"]),
                "cash_balance": float(snap1["cash_balance"]),
                "total_assets": float(snap1["total_assets"]),
            },
            "snapshot2": {
                "id": int(snap2["id"]),
                "date": snap2["snapshot_date"].isoformat(),
                "stock_value": float(snap2["stock_value"]),
                "bank_balance": float(snap2["bank_balance"]),
                "cash_balance": float(snap2["cash_balance"]),
                "total_assets": float(snap2["total_assets"]),
            },
            "difference": float(difference),
            "difference_pct": float(difference_pct),
            "evolution": evolution,
        }

    except SQLAlchemyError as exc:
        LOGGER.error(f"Database error during snapshot comparison: {exc}")
        raise


def get_snapshot_history(
    tenant_id: int,
    days: int = 30,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Get historical snapshots for a tenant.

    Args:
        tenant_id: The tenant ID
        days: Number of days to look back (default: 30)
        limit: Maximum number of snapshots to return (default: 100)

    Returns:
        List of snapshot dictionaries ordered by date descending
    """
    try:
        df = query_df(
            text("""
                SELECT
                    id,
                    snapshot_date,
                    stock_value,
                    bank_balance,
                    cash_balance,
                    total_assets,
                    created_at
                FROM capital_snapshot
                WHERE tenant_id = :tenant_id
                  AND snapshot_date >= CURRENT_DATE - INTERVAL ':days days'
                ORDER BY snapshot_date DESC
                LIMIT :limit
            """),
            params={
                "tenant_id": int(tenant_id),
                "days": days,
                "limit": limit,
            },
        )

        if df.empty:
            return []

        snapshots = []
        for _, row in df.iterrows():
            snapshots.append({
                "id": int(row["id"]),
                "snapshot_date": row["snapshot_date"].isoformat(),
                "stock_value": float(row["stock_value"]),
                "bank_balance": float(row["bank_balance"]),
                "cash_balance": float(row["cash_balance"]),
                "total_assets": float(row["total_assets"]),
                "created_at": row["created_at"].isoformat(),
            })

        return snapshots

    except SQLAlchemyError as exc:
        LOGGER.error(f"Error fetching snapshot history for tenant {tenant_id}: {exc}")
        return []


def delete_snapshot(
    tenant_id: int,
    snapshot_date: date,
) -> bool:
    """
    Delete a snapshot for a specific date.

    Args:
        tenant_id: The tenant ID
        snapshot_date: The date of the snapshot to delete

    Returns:
        True if deleted, False if not found
    """
    eng = get_engine()

    try:
        with eng.begin() as conn:
            result = conn.execute(
                text("""
                    DELETE FROM capital_snapshot
                    WHERE tenant_id = :tenant_id
                      AND snapshot_date::date = :snapshot_date
                    RETURNING id
                """),
                {
                    "tenant_id": int(tenant_id),
                    "snapshot_date": snapshot_date,
                },
            )

            deleted = result.fetchone()

            if deleted:
                LOGGER.info(f"Deleted snapshot for tenant {tenant_id} on {snapshot_date}")
                return True

            return False

    except SQLAlchemyError as exc:
        LOGGER.error(f"Error deleting snapshot for tenant {tenant_id}: {exc}")
        return False
