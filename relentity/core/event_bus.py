import asyncio
import logging
import re
from typing import Dict, List, Any, Awaitable, Pattern, Callable

from .exceptions import InvalidEventNameException, InvalidEventPatternException

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        """
        Initializes the EventBus with an empty dictionary of handlers.
        """
        self.handlers: Dict[Pattern[str], List[Callable[[Any], Awaitable[None]]]] = {}

    def validate_event_name(self, event_name: str) -> None:
        """
        Validates the event name to ensure it matches the required pattern.

        Args:
            event_name (str): The name of the event to validate.

        Raises:
            InvalidEventNameException: If the event name is invalid.
        """
        if not re.match(r"^[a-zA-Z0-9_.]+$", event_name):
            raise InvalidEventNameException(f"Invalid event name: {event_name}")

    def validate_event_pattern(self, event_pattern: str) -> None:
        """
        Validates the event pattern to ensure it matches the required pattern.

        Args:
            event_pattern (str): The pattern of the event to validate.

        Raises:
            InvalidEventPatternException: If the event pattern is invalid.
        """
        if not re.match(r"^[a-zA-Z0-9_.\*]+$", event_pattern):
            raise InvalidEventPatternException(f"Invalid event pattern: {event_pattern}")

    def register_handler(self, event_pattern: str, handler: Callable[[Any], Awaitable[None]]) -> None:
        """
        Registers a handler for a given event pattern.

        Args:
            event_pattern (str): The pattern of the event to register the handler for.
            handler (Callable[[Any], Awaitable[None]]): The handler to register.
        """
        self.validate_event_pattern(event_pattern)
        pattern = re.compile(event_pattern.replace("*", ".*"))
        if pattern not in self.handlers:
            self.handlers[pattern] = []
        self.handlers[pattern].append(handler)
        logger.debug(f"Handler registered for pattern: {event_pattern}")

    async def emit(self, event_name: str, data: Any = None) -> None:
        """
        Emits an event to all handlers that match the event name.

        Args:
            event_name (str): The name of the event to emit.
            data (Any, optional): The data to pass to the handlers. Defaults to None.
        """
        self.validate_event_name(event_name)
        matching_handlers = [
            handler for pattern, handlers in self.handlers.items() if pattern.match(event_name) for handler in handlers
        ]
        if matching_handlers:
            logger.debug(f"Emitting event: {event_name} to {len(matching_handlers)} handlers")
            await asyncio.gather(*[handler(data) for handler in matching_handlers])
        else:
            logger.debug(f"No handlers found for event: {event_name}")
