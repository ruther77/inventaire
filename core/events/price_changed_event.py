"""Price change event for cross-tenant synchronization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class PriceChangedEvent:
    """Event emitted when a product price changes in Épicerie.

    This event is used to notify the Restaurant tenant (tenant_id=2) that
    an Épicerie product (tenant_id=1) has had its price updated, so that
    restaurant food costs can be recalculated.

    Attributes:
        product_id: ID of the product whose price changed
        tenant_id: Tenant ID (should be 1 for Épicerie)
        old_price: Previous prix_achat value (None if new product)
        new_price: New prix_achat value
        changed_at: Timestamp when the price changed
        source: Source of the change (e.g., 'api', 'import', 'invoice')
        metadata: Additional context (e.g., product name, category)
    """

    product_id: int
    tenant_id: int
    old_price: float | None
    new_price: float
    changed_at: datetime
    source: str = "unknown"
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """Validate event data."""
        if self.product_id <= 0:
            raise ValueError("product_id must be positive")
        if self.tenant_id <= 0:
            raise ValueError("tenant_id must be positive")
        if self.new_price < 0:
            raise ValueError("new_price cannot be negative")
        if self.old_price is not None and self.old_price < 0:
            raise ValueError("old_price cannot be negative")

    @property
    def price_change_pct(self) -> float | None:
        """Calculate percentage change in price."""
        if self.old_price is None or self.old_price == 0:
            return None
        return ((self.new_price - self.old_price) / self.old_price) * 100

    @property
    def is_price_increase(self) -> bool:
        """Check if price increased."""
        if self.old_price is None:
            return False
        return self.new_price > self.old_price

    @property
    def is_significant_change(self, threshold_pct: float = 5.0) -> bool:
        """Check if price change exceeds threshold percentage."""
        change_pct = self.price_change_pct
        if change_pct is None:
            return True  # New price is always significant
        return abs(change_pct) >= threshold_pct

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for logging/serialization."""
        return {
            "product_id": self.product_id,
            "tenant_id": self.tenant_id,
            "old_price": self.old_price,
            "new_price": self.new_price,
            "changed_at": self.changed_at.isoformat(),
            "source": self.source,
            "metadata": self.metadata or {},
            "price_change_pct": self.price_change_pct,
            "is_price_increase": self.is_price_increase,
        }
