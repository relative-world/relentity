import time
from typing import Set, Type, Dict, Any, Callable, Awaitable

from .components import Component
from .event_bus import EventBus
from .registry import Registry


class System:
    """An enhanced System base class for processing entities with specific components."""

    # Define required components that this system processes
    required_components: Set[Type[Component]] = set()

    # System execution priority (lower numbers run first)
    priority: int = 100

    def __init__(self, registry: Registry):
        """
        Initialize the System with a registry and default settings.

        Args:
            registry (Registry): The registry to be used by the system.
        """
        self.registry = registry
        self.enabled = True
        self.event_bus = EventBus()
        self.last_execution_time = 0.0
        self.execution_count = 0
        self.average_execution_time = 0.0
        self.config: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """
        Initialize the system. Called once before the system starts updating.
        Override in subclasses to set up resources and event handlers.
        """
        pass

    async def update(self, delta_time: float = 0) -> None:
        """
        Update the system. This method should be overridden by subclasses.

        Args:
            delta_time (float): Time elapsed since the last update in seconds.

        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """
        raise NotImplementedError

    async def process(self, delta_time: float = 0) -> None:
        """
        Process the system if it's enabled, tracking execution time.
        """
        if not self.enabled:
            return

        start_time = time.time()

        try:
            await self.update(delta_time)
        except Exception as e:
            await self.handle_error(e)

        execution_time = time.time() - start_time
        self.last_execution_time = execution_time

        # Update average execution time
        self.execution_count += 1
        self.average_execution_time = (
            self.average_execution_time * (self.execution_count - 1) + execution_time
        ) / self.execution_count

    async def shutdown(self) -> None:
        """
        Clean up resources when the system is being removed.
        Override in subclasses to handle resource cleanup.
        """
        pass

    async def handle_error(self, error: Exception) -> None:
        """
        Handle errors that occur during system update.
        Override in subclasses for custom error handling.

        Args:
            error (Exception): The exception that was raised.
        """
        raise error

    def configure(self, **config) -> "System":
        """
        Configure the system with the given parameters.

        Returns:
            System: The system instance (for method chaining).
        """
        self.config.update(config)
        return self

    def enable(self) -> None:
        """Enable the system."""
        self.enabled = True

    def disable(self) -> None:
        """Disable the system."""
        self.enabled = False

    def register_event_handler(self, event_pattern: str, handler: Callable[[Any], Awaitable[None]]) -> None:
        """
        Register an event handler for this system.

        Args:
            event_pattern (str): The pattern of events to handle.
            handler (Callable): The handler function to call when events occur.
        """
        self.event_bus.register_handler(event_pattern, handler)
