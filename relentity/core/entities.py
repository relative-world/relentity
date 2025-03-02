from typing import Dict, Type, TypeVar, Optional

from .components import Component, T
from .event_bus import EventBus
from .metaclass import EntityMeta

T = TypeVar('T', bound=Component)

class Entity(metaclass=EntityMeta):
    """
    Represents an entity in the system, which can have multiple components and interact with an event bus.

    Attributes:
        components (Dict[Type[Component], Component]): A dictionary of components associated with the entity.
        registry (Registry): The registry to which the entity belongs.
        event_bus (EventBus): The event bus for handling events related to the entity.
    """

    def __init__(self, registry: 'Registry'):
        """
        Initializes a new entity and registers it with the given registry.

        Args:
            registry (Registry): The registry to register the entity with.
        """
        self.components: Dict[Type[Component], Component] = {}
        self.registry = registry
        self.registry.register_entity(self)
        self.event_bus = EventBus()

    def add_component_sync(self, component: Component) -> None:
        """
        Adds a component to the entity synchronously.

        This method is primarily used for the metaclass sugar parts and should be avoided in favor of the async method.

        Args:
            component (Component): The component to add.
        """
        self.components[type(component)] = component
        self.registry.register_entity(self)

    async def add_component(self, component: Component) -> None:
        """
        Adds a component to the entity asynchronously.

        Args:
            component (Component): The component to add.
        """
        self.components[type(component)] = component
        self.registry.register_entity(self)

    async def get_component(self, component_type: Type[T], include_subclasses: bool = False) -> Optional[T]:
        """
        Retrieves a component of the specified type from the entity.

        Args:
            component_type (Type[T]): The type of the component to retrieve.
            include_subclasses (bool): Whether to include subclasses of the component type.

        Returns:
            Optional[T]: The component of the specified type, or None if not found.
        """
        if not include_subclasses:
            return self.components.get(component_type)

        for component in self.components.values():
            if isinstance(component, component_type):
                return component
        return None

    async def has_components(self, *component_types: Type[Component]) -> bool:
        """
        Checks if the entity has all the specified components.

        Args:
            component_types (Type[Component]): The types of components to check for.

        Returns:
            bool: True if the entity has all the specified components, False otherwise.
        """
        for component_type in component_types:
            if await self.get_component(component_type) is None:
                return False
        return True

    async def remove_component(self, component_type: Type[Component]) -> None:
        """
        Removes a component of the specified type from the entity.

        Args:
            component_type (Type[Component]): The type of the component to remove.
        """
        if component_type in self.components:
            self.components.pop(component_type)
