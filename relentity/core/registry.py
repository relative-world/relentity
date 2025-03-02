from typing import Set, Dict, Type, AsyncIterator

from .entities import Entity
from .components import Component

class Registry:
    def __init__(self):
        """
        Initializes the Registry with an empty set of entities and a dictionary
        mapping component types to sets of entities.
        """
        self.entities: Set[Entity] = set()
        self.component_to_entities: Dict[Type[Component], Set[Entity]] = {}

    def register_entity(self, entity: Entity) -> None:
        """
        Registers an entity with the registry and updates the component-to-entities mapping.

        Args:
            entity (Entity): The entity to register.
        """
        self.entities.add(entity)
        for component_type in entity.components:
            if component_type not in self.component_to_entities:
                self.component_to_entities[component_type] = set()
            self.component_to_entities[component_type].add(entity)

    async def entities_with_components(self, *component_types: Type[Component], include_subclasses: bool = False) -> AsyncIterator[Entity]:
        """
        Yields entities that have all the specified components.

        Args:
            component_types (Type[Component]): The types of components to check for.
            include_subclasses (bool): Whether to include subclasses of the component types.

        Yields:
            Entity: An entity that has all the specified components.
        """
        if not component_types:
            raise StopAsyncIteration

        if include_subclasses:
            for entity in self.entities:
                if all([await entity.get_component(component_type, include_subclasses) for component_type in component_types]):
                    yield entity
        else:
            entities = set(self.component_to_entities.get(component_types[0], []))
            for component_type in component_types[1:]:
                entities &= set(self.component_to_entities.get(component_type, []))
            for entity in list(entities):
                yield entity

    async def remove_component_from_entity(self, entity: Entity, component_type: Type[Component]) -> None:
        """
        Removes a component of the specified type from an entity and updates the registry.

        Args:
            entity (Entity): The entity to remove the component from.
            component_type (Type[Component]): The type of the component to remove.
        """
        entity.components.pop(component_type, None)
        self.component_to_entities[component_type].remove(entity)
        if not entity.components:
            self.entities.remove(entity)
