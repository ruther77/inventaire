"""Simple in-process event dispatcher for pub/sub pattern."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

from core.events.price_changed_event import PriceChangedEvent

LOGGER = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[Any], None]


class EventDispatcher:
    """Simple synchronous event dispatcher for in-process pub/sub.

    This dispatcher allows components to subscribe to events and receive
    notifications when events are published. Handlers are called synchronously
    in the order they were registered.

    Example:
        dispatcher = EventDispatcher()

        def on_price_change(event: PriceChangedEvent):
            print(f"Price changed for product {event.product_id}")

        dispatcher.subscribe(PriceChangedEvent, on_price_change)
        dispatcher.publish(PriceChangedEvent(
            product_id=1,
            tenant_id=1,
            old_price=10.0,
            new_price=12.0,
            changed_at=datetime.now()
        ))
    """

    def __init__(self):
        """Initialize the event dispatcher."""
        self._handlers: dict[type, list[EventHandler]] = defaultdict(list)
        self._enabled = True

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: The event class to subscribe to (e.g., PriceChangedEvent)
            handler: Callable that will be invoked when event is published
        """
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            LOGGER.debug(f"Subscribed {handler.__name__} to {event_type.__name__}")

    def unsubscribe(self, event_type: type, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type.

        Args:
            event_type: The event class to unsubscribe from
            handler: The handler to remove
        """
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            LOGGER.debug(f"Unsubscribed {handler.__name__} from {event_type.__name__}")

    def publish(self, event: Any) -> None:
        """Publish an event to all subscribed handlers.

        Handlers are called synchronously in registration order. If a handler
        raises an exception, it is logged but does not prevent other handlers
        from being called.

        Args:
            event: The event instance to publish
        """
        if not self._enabled:
            LOGGER.debug(f"Dispatcher disabled, skipping event {type(event).__name__}")
            return

        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            LOGGER.debug(f"No handlers registered for {event_type.__name__}")
            return

        LOGGER.info(f"Publishing {event_type.__name__} to {len(handlers)} handler(s)")

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                LOGGER.error(
                    f"Error in handler {handler.__name__} for {event_type.__name__}: {e}",
                    exc_info=True,
                )

    def clear(self, event_type: type | None = None) -> None:
        """Clear all handlers for an event type, or all handlers if None.

        Args:
            event_type: Event type to clear handlers for, or None to clear all
        """
        if event_type is None:
            self._handlers.clear()
            LOGGER.debug("Cleared all event handlers")
        else:
            self._handlers[event_type].clear()
            LOGGER.debug(f"Cleared handlers for {event_type.__name__}")

    def disable(self) -> None:
        """Disable event dispatching temporarily."""
        self._enabled = False
        LOGGER.info("Event dispatcher disabled")

    def enable(self) -> None:
        """Re-enable event dispatching."""
        self._enabled = True
        LOGGER.info("Event dispatcher enabled")

    @property
    def is_enabled(self) -> bool:
        """Check if dispatcher is enabled."""
        return self._enabled

    def get_handler_count(self, event_type: type) -> int:
        """Get number of handlers registered for an event type."""
        return len(self._handlers.get(event_type, []))


# Global singleton instance
_dispatcher: EventDispatcher | None = None


def get_event_dispatcher() -> EventDispatcher:
    """Get or create the global event dispatcher instance.

    Returns:
        The singleton EventDispatcher instance
    """
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = EventDispatcher()
        LOGGER.info("Created global event dispatcher")
    return _dispatcher


def reset_event_dispatcher() -> None:
    """Reset the global dispatcher (mainly for testing)."""
    global _dispatcher
    _dispatcher = None
    LOGGER.debug("Reset global event dispatcher")
