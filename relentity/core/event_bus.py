import asyncio
import logging
import re
from typing import Dict, List, Any, Awaitable, Pattern

from .exceptions import InvalidEventNameException, InvalidEventPatternException

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self.handlers: Dict[Pattern[str], List[Awaitable]] = {}

    def validate_event_name(self, event_name: str):
        if not re.match(r'^[a-zA-Z0-9_.]+$', event_name):
            raise InvalidEventNameException(f"Invalid event name: {event_name}")

    def validate_event_pattern(self, event_pattern: str):
        if not re.match(r'^[a-zA-Z0-9_.\*]+$', event_pattern):
            raise InvalidEventPatternException(f"Invalid event pattern: {event_pattern}")

    def register_handler(self, event_pattern: str, handler: Awaitable):
        self.validate_event_pattern(event_pattern)
        pattern = re.compile(event_pattern.replace('*', '.*'))
        if pattern not in self.handlers:
            self.handlers[pattern] = []
        self.handlers[pattern].append(handler)
        logger.debug(f"Handler registered for pattern: {event_pattern}")

    async def emit(self, event_name: str, data: Any = None):
        self.validate_event_name(event_name)
        matching_handlers = [
            handler
            for pattern, handlers in self.handlers.items()
            if pattern.match(event_name)
            for handler in handlers
        ]
        if matching_handlers:
            logger.debug(f"Emitting event: {event_name} to {len(matching_handlers)} handlers")
            await asyncio.gather(*[handler(data) for handler in matching_handlers])
        else:
            logger.debug(f"No handlers found for event: {event_name}")
