import asyncio
from typing import Dict, List, Any, Awaitable


class EventBus:
    def __init__(self):
        self.handlers: Dict[str, List[Awaitable]] = {}

    def register_handler(self, event_name: str, handler: Awaitable):
        if event_name not in self.handlers:
            self.handlers[event_name] = []
        self.handlers[event_name].append(handler)

    async def emit(self, event_name: str, data: Any = None):
        if event_name in self.handlers:
            await asyncio.gather(*[handler(data) for handler in self.handlers[event_name]])
