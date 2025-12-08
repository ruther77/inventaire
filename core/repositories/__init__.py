"""
Repository Layer - Clean Architecture pattern for data access.

This module provides:
- Base repository protocols with common CRUD operations
- Concrete SQL implementations using SQLAlchemy
- Unit of Work pattern for transaction management
"""

from .base import (
    Repository,
    ReadOnlyRepository,
    UnitOfWork,
)
from .users import UserRepository, SqlUserRepository
from .stock_movements import StockMovementRepository, SqlStockMovementRepository

__all__ = [
    # Base
    "Repository",
    "ReadOnlyRepository",
    "UnitOfWork",
    # Users
    "UserRepository",
    "SqlUserRepository",
    # Stock
    "StockMovementRepository",
    "SqlStockMovementRepository",
]
