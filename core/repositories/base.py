"""
Base Repository - Generic repository interfaces using Protocol.

Implements the Repository pattern for clean separation between
business logic and data access.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, Protocol, Sequence, Any
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.engine import Engine, Connection

T = TypeVar("T")
ID = TypeVar("ID", int, str)


class ReadOnlyRepository(Protocol[T, ID]):
    """Read-only repository interface."""

    @abstractmethod
    def get_by_id(self, id: ID, *, tenant_id: int) -> T | None:
        """Get entity by ID."""
        ...

    @abstractmethod
    def list_all(self, *, tenant_id: int, limit: int = 100, offset: int = 0) -> Sequence[T]:
        """List all entities with pagination."""
        ...

    @abstractmethod
    def count(self, *, tenant_id: int) -> int:
        """Count total entities."""
        ...


class Repository(ReadOnlyRepository[T, ID], Protocol):
    """Full repository interface with write operations."""

    @abstractmethod
    def add(self, entity: T, *, tenant_id: int) -> T:
        """Add new entity and return it with generated ID."""
        ...

    @abstractmethod
    def update(self, entity: T, *, tenant_id: int) -> T:
        """Update existing entity."""
        ...

    @abstractmethod
    def delete(self, id: ID, *, tenant_id: int) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        ...


class UnitOfWork(Protocol):
    """
    Unit of Work pattern for managing transactions.

    Usage:
        with uow:
            uow.users.add(user, tenant_id=1)
            uow.products.update(product, tenant_id=1)
            uow.commit()
    """

    @abstractmethod
    def __enter__(self) -> "UnitOfWork":
        ...

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        ...

    @abstractmethod
    def commit(self) -> None:
        """Commit all changes."""
        ...

    @abstractmethod
    def rollback(self) -> None:
        """Rollback all changes."""
        ...


@dataclass
class PagedResult(Generic[T]):
    """Container for paginated results."""

    items: Sequence[T]
    total: int
    page: int
    per_page: int

    @property
    def total_pages(self) -> int:
        if self.per_page <= 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


class SqlUnitOfWork:
    """
    SQLAlchemy implementation of Unit of Work.

    Manages a single database transaction across multiple repositories.
    """

    def __init__(self, engine: Engine):
        self._engine = engine
        self._connection: Connection | None = None

    def __enter__(self) -> "SqlUnitOfWork":
        self._connection = self._engine.connect()
        self._transaction = self._connection.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
        if self._connection:
            self._connection.close()
        self._connection = None

    @property
    def connection(self) -> Connection:
        if self._connection is None:
            raise RuntimeError("UnitOfWork not started. Use 'with' statement.")
        return self._connection

    def commit(self) -> None:
        if self._transaction:
            self._transaction.commit()

    def rollback(self) -> None:
        if self._transaction:
            self._transaction.rollback()
