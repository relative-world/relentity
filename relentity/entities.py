from typing import Dict, Type

from relentity.components import Component
from relentity.metaclasses import EntityMeta
from relentity.registry import Registry


class Entity(metaclass=EntityMeta):
    def __init__(self, registry: Registry):
        self.components: Dict[Type[Component], Component] = {}
        self.registry = registry
        self.registry.register_entity(self)

    def add_component(self, component: Component):
        self.components[type(component)] = component
        self.registry.register_entity(self)

    def get_component(self, component_type: Type[Component.T]) -> Component.T:
        return self.components.get(component_type)
