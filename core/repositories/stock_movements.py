"""
Stock Movement Repository - Data access for mouvements_stock table.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Protocol, Sequence

from sqlalchemy import text

from core.data_repository import get_engine, query_df, exec_sql_return_id


class MovementType(str, Enum):
    ENTREE = "ENTREE"
    SORTIE = "SORTIE"
    TRANSFERT = "TRANSFERT"
    INVENTAIRE = "INVENTAIRE"


@dataclass
class StockMovement:
    """Stock movement entity."""

    id: int | None
    produit_id: int
    type: MovementType
    quantite: Decimal
    source: str | None
    tenant_id: int
    date_mvt: datetime | None = None
    created_at: datetime | None = None


@dataclass
class StockMovementSummary:
    """Aggregated stock movement data."""

    date: date
    total_entrees: Decimal
    total_sorties: Decimal
    net: Decimal


class StockMovementRepository(Protocol):
    """Stock movement repository interface."""

    def get_by_id(self, id: int, *, tenant_id: int) -> StockMovement | None:
        ...

    def list_by_product(
        self, produit_id: int, *, tenant_id: int, limit: int = 100
    ) -> Sequence[StockMovement]:
        ...

    def list_recent(
        self, *, tenant_id: int, days: int = 30, limit: int = 100
    ) -> Sequence[StockMovement]:
        ...

    def add(self, movement: StockMovement) -> StockMovement:
        ...

    def get_weekly_summary(
        self, *, tenant_id: int, weeks: int = 8
    ) -> Sequence[StockMovementSummary]:
        ...

    def get_daily_totals(
        self, *, tenant_id: int, start_date: date, end_date: date
    ) -> Sequence[StockMovementSummary]:
        ...


class SqlStockMovementRepository:
    """SQLAlchemy implementation of StockMovementRepository."""

    def __init__(self):
        self._engine = get_engine()

    def get_by_id(self, id: int, *, tenant_id: int) -> StockMovement | None:
        sql = text(
            """
            SELECT id, produit_id, type, quantite, source, tenant_id, date_mvt, created_at
            FROM mouvements_stock
            WHERE id = :id AND tenant_id = :tenant_id
            """
        )
        df = query_df(sql, {"id": id, "tenant_id": tenant_id})
        if df.empty:
            return None
        return self._row_to_movement(df.iloc[0].to_dict())

    def list_by_product(
        self, produit_id: int, *, tenant_id: int, limit: int = 100
    ) -> Sequence[StockMovement]:
        sql = text(
            """
            SELECT id, produit_id, type, quantite, source, tenant_id, date_mvt, created_at
            FROM mouvements_stock
            WHERE produit_id = :produit_id AND tenant_id = :tenant_id
            ORDER BY date_mvt DESC
            LIMIT :limit
            """
        )
        df = query_df(
            sql, {"produit_id": produit_id, "tenant_id": tenant_id, "limit": limit}
        )
        return [self._row_to_movement(row) for row in df.to_dict("records")]

    def list_recent(
        self, *, tenant_id: int, days: int = 30, limit: int = 100
    ) -> Sequence[StockMovement]:
        sql = text(
            """
            SELECT id, produit_id, type, quantite, source, tenant_id, date_mvt, created_at
            FROM mouvements_stock
            WHERE tenant_id = :tenant_id
              AND date_mvt >= NOW() - INTERVAL ':days days'
            ORDER BY date_mvt DESC
            LIMIT :limit
            """
        )
        df = query_df(sql, {"tenant_id": tenant_id, "days": days, "limit": limit})
        return [self._row_to_movement(row) for row in df.to_dict("records")]

    def add(self, movement: StockMovement) -> StockMovement:
        sql = text(
            """
            INSERT INTO mouvements_stock (produit_id, type, quantite, source, tenant_id, date_mvt)
            VALUES (:produit_id, :type, :quantite, :source, :tenant_id, COALESCE(:date_mvt, NOW()))
            RETURNING id, date_mvt, created_at
            """
        )
        params = {
            "produit_id": movement.produit_id,
            "type": movement.type.value if isinstance(movement.type, MovementType) else movement.type,
            "quantite": float(movement.quantite),
            "source": movement.source,
            "tenant_id": movement.tenant_id,
            "date_mvt": movement.date_mvt,
        }
        engine = get_engine()
        with engine.begin() as conn:
            result = conn.execute(sql, params)
            row = result.fetchone()
            if row:
                movement.id = row[0]
                movement.date_mvt = row[1]
                movement.created_at = row[2]
        return movement

    def get_weekly_summary(
        self, *, tenant_id: int, weeks: int = 8
    ) -> Sequence[StockMovementSummary]:
        sql = text(
            """
            SELECT
                DATE_TRUNC('week', date_mvt)::date AS date,
                COALESCE(SUM(CASE WHEN type = 'ENTREE' THEN quantite ELSE 0 END), 0) AS total_entrees,
                COALESCE(SUM(CASE WHEN type = 'SORTIE' THEN quantite ELSE 0 END), 0) AS total_sorties,
                COALESCE(
                    SUM(CASE WHEN type = 'ENTREE' THEN quantite ELSE 0 END) -
                    SUM(CASE WHEN type = 'SORTIE' THEN quantite ELSE 0 END),
                    0
                ) AS net
            FROM mouvements_stock
            WHERE tenant_id = :tenant_id
              AND date_mvt >= NOW() - INTERVAL ':weeks weeks'
            GROUP BY DATE_TRUNC('week', date_mvt)
            ORDER BY date DESC
            """
        )
        df = query_df(sql, {"tenant_id": tenant_id, "weeks": weeks})
        return [
            StockMovementSummary(
                date=row["date"],
                total_entrees=Decimal(str(row["total_entrees"])),
                total_sorties=Decimal(str(row["total_sorties"])),
                net=Decimal(str(row["net"])),
            )
            for row in df.to_dict("records")
        ]

    def get_daily_totals(
        self, *, tenant_id: int, start_date: date, end_date: date
    ) -> Sequence[StockMovementSummary]:
        sql = text(
            """
            SELECT
                date_mvt::date AS date,
                COALESCE(SUM(CASE WHEN type = 'ENTREE' THEN quantite ELSE 0 END), 0) AS total_entrees,
                COALESCE(SUM(CASE WHEN type = 'SORTIE' THEN quantite ELSE 0 END), 0) AS total_sorties,
                COALESCE(
                    SUM(CASE WHEN type = 'ENTREE' THEN quantite ELSE 0 END) -
                    SUM(CASE WHEN type = 'SORTIE' THEN quantite ELSE 0 END),
                    0
                ) AS net
            FROM mouvements_stock
            WHERE tenant_id = :tenant_id
              AND date_mvt >= :start_date
              AND date_mvt < :end_date + INTERVAL '1 day'
            GROUP BY date_mvt::date
            ORDER BY date DESC
            """
        )
        df = query_df(
            sql,
            {"tenant_id": tenant_id, "start_date": start_date, "end_date": end_date},
        )
        return [
            StockMovementSummary(
                date=row["date"],
                total_entrees=Decimal(str(row["total_entrees"])),
                total_sorties=Decimal(str(row["total_sorties"])),
                net=Decimal(str(row["net"])),
            )
            for row in df.to_dict("records")
        ]

    def _row_to_movement(self, row: dict) -> StockMovement:
        return StockMovement(
            id=row["id"],
            produit_id=row["produit_id"],
            type=MovementType(row["type"]),
            quantite=Decimal(str(row["quantite"])),
            source=row.get("source"),
            tenant_id=row["tenant_id"],
            date_mvt=row.get("date_mvt"),
            created_at=row.get("created_at"),
        )
