import asyncio
import uuid
from typing import Dict, Type, Optional, TYPE_CHECKING

from .components import Component, T
from .event_bus import EventBus
from .events import (
    ENTITY_COMPONENT_UPDATED_EVENT,
    ENTITY_COMPONENT_ADDED_EVENT,
    ENTITY_CREATED_EVENT,
)
from .metaclass import EntityMeta

if TYPE_CHECKING:
    from .registry import Registry
    from .entity_ref import EntityRef


class Entity(metaclass=EntityMeta):
    """
    Represents an entity in the system, which can have multiple components and interact with an event bus.

    Attributes:
        components (Dict[Type[Component], Component]): A dictionary of components associated with the entity.
        registry (Registry): The registry to which the entity belongs.
        event_bus (EventBus): The event bus for handling events related to the entity.
    """

    def __init__(self, registry: "Registry"):
        """
        Initializes a new entity and registers it with the given registry.

        Args:
            registry (Registry): The registry to register the entity with.
        """
        self.id = uuid.uuid4()
        self.components: Dict[Type[Component], Component] = {}
        self.registry = registry
        self.registry.register_entity(self)
        self.event_bus = EventBus()
        # Emit creation event
        asyncio.create_task(self.event_bus.emit(ENTITY_CREATED_EVENT, self))

    @property
    def entity_ref(self) -> "EntityRef":
        return self.registry.get_entity_ref(self.id)

    def add_component_sync(self, component: Component) -> None:
        """
        Adds a component to the entity synchronously.

        Args:
            component (Component): The component to add.
        """
        component_type = type(component)
        is_update = component_type in self.components
        self.components[component_type] = component
        self.registry.register_entity(self)

        if is_update:
            asyncio.create_task(self.event_bus.emit(ENTITY_COMPONENT_UPDATED_EVENT, (self, component)))
        else:
            asyncio.create_task(self.event_bus.emit(ENTITY_COMPONENT_ADDED_EVENT, (self, component)))

    async def add_component(self, component: Component) -> None:
        """
        Adds a component to the entity asynchronously.

        Args:
            component (Component): The component to add.
        """
        component_type = type(component)
        is_update = component_type in self.components
        self.components[component_type] = component
        self.registry.register_entity(self)

        if is_update:
            await self.event_bus.emit(ENTITY_COMPONENT_UPDATED_EVENT, (self, component))
        else:
            await self.event_bus.emit(ENTITY_COMPONENT_ADDED_EVENT, (self, component))

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

        for other_component_type, component in list(self.components.items()):
            if issubclass(other_component_type, component_type):
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

    async def destroy(self) -> None:
        """
        Properly destroy this entity, cleaning up all references.
        """
        await self.registry.unregister_entity(self.id)
        # Clear components
        self.components.clear()


def attach_components_sync(entity, *components) -> None:
    # Add each component to the entity
    async def _inner():
        for component in components:
            if isinstance(component, Component):
                # If the component is an instance of Component, add it directly
                await entity.add_component(component.model_copy())
            elif callable(component):
                # If the component is a callable, call it to get the Component instance and add it
                await entity.add_component(component())
            else:
                # Raise an error if the component is neither a Component instance nor a callable
                raise TypeError("Component must be a Component instance or a callable")

    asyncio.create_task(_inner())
