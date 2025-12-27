"""Soft delete utilities for critical tables.

Provides functions to soft delete records, restore them, and filter queries
to exclude deleted records for audit trail and data recovery.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from .data_repository import get_engine


class SoftDeleteError(Exception):
    """Base exception for soft delete operations."""


class RecordNotFoundError(SoftDeleteError):
    """Raised when a record is not found."""


class RecordAlreadyDeletedError(SoftDeleteError):
    """Raised when trying to delete an already deleted record."""


class RecordNotDeletedError(SoftDeleteError):
    """Raised when trying to restore a record that is not deleted."""


# Tables that support soft delete
SOFT_DELETE_TABLES = {
    "produits",
    "finance_transactions",
    "processed_invoices",
    "restaurant_plats",
}


def _validate_table(table: str) -> None:
    """Validate that the table supports soft delete."""
    if table not in SOFT_DELETE_TABLES:
        raise SoftDeleteError(
            f"Table '{table}' does not support soft delete. "
            f"Supported tables: {', '.join(sorted(SOFT_DELETE_TABLES))}"
        )


def soft_delete(
    table: str,
    record_id: int,
    user: str,
    conn: Optional[Connection] = None,
    engine: Optional[Engine] = None,
) -> dict[str, Any]:
    """Soft delete a record by setting deleted_at and deleted_by.

    Args:
        table: Name of the table (must be in SOFT_DELETE_TABLES)
        record_id: ID of the record to delete
        user: Username or identifier of the user performing the deletion
        conn: Optional SQLAlchemy connection (if in a transaction)
        engine: Optional SQLAlchemy engine (uses default if not provided)

    Returns:
        dict: The deleted record data

    Raises:
        SoftDeleteError: If table is not supported
        RecordNotFoundError: If record does not exist
        RecordAlreadyDeletedError: If record is already deleted
    """
    _validate_table(table)

    if conn is None:
        if engine is None:
            engine = get_engine()
        return _soft_delete_with_engine(table, record_id, user, engine)
    else:
        return _soft_delete_with_conn(table, record_id, user, conn)


def _soft_delete_with_engine(
    table: str, record_id: int, user: str, engine: Engine
) -> dict[str, Any]:
    """Soft delete using an engine (creates its own transaction)."""
    with engine.begin() as conn:
        return _soft_delete_with_conn(table, record_id, user, conn)


def _soft_delete_with_conn(
    table: str, record_id: int, user: str, conn: Connection
) -> dict[str, Any]:
    """Soft delete using an existing connection."""
    # Check if record exists
    check_query = text(f"SELECT id, deleted_at FROM {table} WHERE id = :id")
    result = conn.execute(check_query, {"id": record_id}).fetchone()

    if result is None:
        raise RecordNotFoundError(f"Record {record_id} not found in table {table}")

    if result[1] is not None:  # deleted_at is not NULL
        raise RecordAlreadyDeletedError(
            f"Record {record_id} in table {table} is already deleted"
        )

    # Perform soft delete
    now = datetime.now(timezone.utc)
    update_query = text(f"""
        UPDATE {table}
        SET deleted_at = :deleted_at,
            deleted_by = :deleted_by
        WHERE id = :id
        RETURNING *
    """)

    deleted_record = conn.execute(
        update_query,
        {"id": record_id, "deleted_at": now, "deleted_by": user}
    ).fetchone()

    return dict(deleted_record._mapping) if deleted_record else {}


def restore(
    table: str,
    record_id: int,
    conn: Optional[Connection] = None,
    engine: Optional[Engine] = None,
) -> dict[str, Any]:
    """Restore a soft-deleted record by clearing deleted_at and deleted_by.

    Args:
        table: Name of the table (must be in SOFT_DELETE_TABLES)
        record_id: ID of the record to restore
        conn: Optional SQLAlchemy connection (if in a transaction)
        engine: Optional SQLAlchemy engine (uses default if not provided)

    Returns:
        dict: The restored record data

    Raises:
        SoftDeleteError: If table is not supported
        RecordNotFoundError: If record does not exist
        RecordNotDeletedError: If record is not deleted
    """
    _validate_table(table)

    if conn is None:
        if engine is None:
            engine = get_engine()
        return _restore_with_engine(table, record_id, engine)
    else:
        return _restore_with_conn(table, record_id, conn)


def _restore_with_engine(table: str, record_id: int, engine: Engine) -> dict[str, Any]:
    """Restore using an engine (creates its own transaction)."""
    with engine.begin() as conn:
        return _restore_with_conn(table, record_id, conn)


def _restore_with_conn(table: str, record_id: int, conn: Connection) -> dict[str, Any]:
    """Restore using an existing connection."""
    # Check if record exists and is deleted
    check_query = text(f"SELECT id, deleted_at FROM {table} WHERE id = :id")
    result = conn.execute(check_query, {"id": record_id}).fetchone()

    if result is None:
        raise RecordNotFoundError(f"Record {record_id} not found in table {table}")

    if result[1] is None:  # deleted_at is NULL
        raise RecordNotDeletedError(
            f"Record {record_id} in table {table} is not deleted"
        )

    # Perform restore
    update_query = text(f"""
        UPDATE {table}
        SET deleted_at = NULL,
            deleted_by = NULL
        WHERE id = :id
        RETURNING *
    """)

    restored_record = conn.execute(update_query, {"id": record_id}).fetchone()

    return dict(restored_record._mapping) if restored_record else {}


def add_not_deleted_filter(sql: str, table_alias: Optional[str] = None) -> str:
    """Add WHERE clause to filter out soft-deleted records.

    Args:
        sql: The SQL query string
        table_alias: Optional table alias to use (e.g., 'p' for 'p.deleted_at IS NULL')

    Returns:
        str: Modified SQL query with soft delete filter

    Examples:
        >>> add_not_deleted_filter("SELECT * FROM produits")
        'SELECT * FROM produits WHERE deleted_at IS NULL'

        >>> add_not_deleted_filter("SELECT * FROM produits p WHERE p.actif = true", "p")
        'SELECT * FROM produits p WHERE p.actif = true AND p.deleted_at IS NULL'
    """
    prefix = f"{table_alias}." if table_alias else ""
    condition = f"{prefix}deleted_at IS NULL"

    # Check if query already has a WHERE clause
    if " WHERE " in sql.upper():
        # Add to existing WHERE clause
        return f"{sql} AND {condition}"
    else:
        # Add new WHERE clause
        # Find position to insert (before ORDER BY, LIMIT, GROUP BY, etc.)
        for keyword in [" ORDER BY ", " LIMIT ", " GROUP BY ", " HAVING ", " OFFSET "]:
            if keyword in sql.upper():
                pos = sql.upper().find(keyword)
                return f"{sql[:pos]} WHERE {condition} {sql[pos:]}"
        # No limiting clause found, append at end
        return f"{sql} WHERE {condition}"


def get_deleted_records(
    table: str,
    limit: int = 100,
    offset: int = 0,
    conn: Optional[Connection] = None,
    engine: Optional[Engine] = None,
) -> list[dict[str, Any]]:
    """Get a list of soft-deleted records from a table.

    Args:
        table: Name of the table (must be in SOFT_DELETE_TABLES)
        limit: Maximum number of records to return
        offset: Number of records to skip
        conn: Optional SQLAlchemy connection
        engine: Optional SQLAlchemy engine (uses default if not provided)

    Returns:
        list[dict]: List of deleted records

    Raises:
        SoftDeleteError: If table is not supported
    """
    _validate_table(table)

    query = text(f"""
        SELECT *
        FROM {table}
        WHERE deleted_at IS NOT NULL
        ORDER BY deleted_at DESC
        LIMIT :limit OFFSET :offset
    """)

    if conn is not None:
        result = conn.execute(query, {"limit": limit, "offset": offset})
        return [dict(row._mapping) for row in result.fetchall()]
    else:
        if engine is None:
            engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(query, {"limit": limit, "offset": offset})
            return [dict(row._mapping) for row in result.fetchall()]


def count_deleted_records(
    table: str,
    conn: Optional[Connection] = None,
    engine: Optional[Engine] = None,
) -> int:
    """Count the number of soft-deleted records in a table.

    Args:
        table: Name of the table (must be in SOFT_DELETE_TABLES)
        conn: Optional SQLAlchemy connection
        engine: Optional SQLAlchemy engine (uses default if not provided)

    Returns:
        int: Number of deleted records

    Raises:
        SoftDeleteError: If table is not supported
    """
    _validate_table(table)

    query = text(f"SELECT COUNT(*) FROM {table} WHERE deleted_at IS NOT NULL")

    if conn is not None:
        result = conn.execute(query).scalar()
        return int(result) if result else 0
    else:
        if engine is None:
            engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(query).scalar()
            return int(result) if result else 0
