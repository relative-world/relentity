from typing import Dict, Type

from relentity.components import Component, T
from relentity.event_bus import EventBus
from relentity.metaclass import EntityMeta
from relentity.registry import Registry


class Entity(metaclass=EntityMeta):
    def __init__(self, registry: Registry):
        self.components: Dict[Type[Component], Component] = {}
        self.registry = registry
        self.registry.register_entity(self)
        self.event_bus = EventBus()

    def add_component_sync(self, component: Component):
        self.components[type(component)] = component
        self.registry.register_entity(self)

    async def add_component(self, component: Component):
        self.components[type(component)] = component
        self.registry.register_entity(self)

    async def get_component(self, component_type: Type[T]) -> T:
        return self.components.get(component_type)
