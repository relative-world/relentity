from typing import Dict, Type

from .components import Component, T
from .event_bus import EventBus
from .metaclass import EntityMeta
from .registry import Registry


class Entity(metaclass=EntityMeta):
    def __init__(self, registry: Registry):
        self.components: Dict[Type[Component], Component] = {}
        self.registry = registry
        self.registry.register_entity(self)
        self.event_bus = EventBus()

    def add_component_sync(self, component: Component):
        """
        Only used for the sugar parts of the metaclass

        Since the metaclass is a bit of a hack, we need to add components synchronously
        because __init__ methods can't be async

        still, we want to keep the async/await pattern for the rest of the codebase

        If you're using this method, you're probably doing something wrong
        """
        self.components[type(component)] = component
        self.registry.register_entity(self)

    async def add_component(self, component: Component):
        self.components[type(component)] = component
        self.registry.register_entity(self)

    async def get_component(self, component_type: Type[T], include_subclasses: bool = False) -> T:
        if not include_subclasses:
            return self.components.get(component_type)

        for _, component in self.components.items():
            if isinstance(component, component_type):
                return component

    async def has_components(self, *component_types: Type[Component]) -> bool:
        return all(await self.get_component(component_type) for component_type in component_types)

    async def remove_component(self, component_type: Type[Component]):
        if component_type in self.components:
            self.components.pop(component_type)
