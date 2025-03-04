import uuid
from typing import Set, Dict, Type, AsyncIterator, TYPE_CHECKING

from .components import Component
from .entity_ref import EntityRef
from .events import ENTITY_DESTROYED_EVENT
from .exceptions import UnknownEntityError, UnknownComponentError

if TYPE_CHECKING:
    from .entities import Entity


class Registry:
    def __init__(self):
        """
        Initializes the Registry with an empty set of entities and a dictionary
        mapping component types to sets of entities.
        """
        self.entities: Dict[uuid.UUID, Entity] = {}
        self.component_to_entity_ids: Dict[Type[Component], Set[uuid.UUID]] = {}

    def register_entity(self, entity: "Entity") -> None:
        """
        Registers an entity with the registry and updates the component-to-entities mapping.

        Args:
            entity (Entity): The entity to register.
        """
        self.entities[entity.id] = entity

        for component_type in entity.components:
            if component_type not in self.component_to_entity_ids:
                self.component_to_entity_ids[component_type] = set()
            self.component_to_entity_ids[component_type].add(entity.id)

    async def unregister_entity(self, entity_id) -> None:
        """Remove an entity completely from the registry."""
        entity = await self.get_entity_by_id(entity_id)
        del self.entities[entity_id]

        # Remove from component mappings
        for component_type in list(entity.components.keys()):
            if component_type in self.component_to_entity_ids:
                self.component_to_entity_ids[component_type].discard(entity)

        # Emit destruction event via entity's event bus
        await entity.event_bus.emit(ENTITY_DESTROYED_EVENT, entity)

    async def entities_with_components(
        self, *component_types: Type[Component], include_subclasses: bool = False
    ) -> AsyncIterator[EntityRef]:
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
            for entity in list(self.entities.values()):
                if all(
                    [
                        await entity.get_component(component_type, include_subclasses)
                        for component_type in component_types
                    ]
                ):
                    yield EntityRef(entity_id=entity.id, _registry=self)
        else:
            entity_ids = set(self.component_to_entity_ids.get(component_types[0], []))
            for component_type in component_types[1:]:
                entity_ids &= set(self.component_to_entity_ids.get(component_type, []))
            for entity_id in list(entity_ids):
                yield EntityRef(entity_id=entity_id, _registry=self)

    async def remove_component_from_entity(self, entity_id: uuid.UUID, component_type: Type[Component]) -> None:
        """
        Removes a component of the specified type from an entity and updates the registry.

        Args:
            entity (Entity): The entity to remove the component from.
            component_type (Type[Component]): The type of the component to remove.
        """
        entity = await self.get_entity_by_id(entity_id)

        try:
            entity.components.pop(component_type)
        except KeyError as exc:
            raise UnknownComponentError(component_type) from exc

        try:
            self.component_to_entity_ids[component_type].remove(entity_id)
        except KeyError:
            pass

        # clean up the entity if it has no components
        if not entity.components:
            del self.entities[entity.id]

    async def get_entity_by_id(self, entity_id) -> "Entity":
        try:
            return self.entities[entity_id]
        except KeyError:
            raise UnknownEntityError(entity_id)

    def get_entity_ref(self, entity_id: uuid.UUID) -> EntityRef:
        return EntityRef(entity_id=entity_id, _registry=self)
