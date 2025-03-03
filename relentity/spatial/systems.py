from relentity.core.systems import System
from .components import Position, Velocity, Vision, Audible, Hearing, Visible, Area, Located
from .events import (
    EntitySeenEvent,
    ENTITY_SEEN_EVENT_TYPE,
    POSITION_UPDATED_EVENT_TYPE,
    SOUND_HEARD_EVENT_TYPE,
    AreaEvent,
)
from .events import SOUND_CREATED_EVENT_TYPE, AREA_ENTERED_EVENT_TYPE, AREA_EXITED_EVENT_TYPE
from .registry import SpatialRegistry
from ..core import Entity
from ..core.entity_ref import EntityRef
from ..core.exceptions import UnknownComponentError


class SpatialSystem(System):
    """
    Base class for spatial systems, providing common functionality for systems that operate on spatial entities.

    Args:
        registry (SpatialRegistry): The registry to be used by the system.
    """

    def __init__(self, registry: SpatialRegistry):
        """
        Initializes the SpatialSystem with a registry.

        Args:
            registry (SpatialRegistry): The registry to be used by the system.
        """
        super().__init__(registry)
        self.registry = registry


class MovementSystem(SpatialSystem):
    """
    System for updating the positions of entities based on their velocities.

    Attributes:
        max_speed (float): The maximum speed an entity can move.
    """

    max_speed = 30

    async def update(self):
        """
        Updates the positions of entities with Position and Velocity components.
        Limits the speed of entities to max_speed.
        Emits a POSITION_UPDATED_EVENT_TYPE event after updating the position.
        """
        async for entity_ref in self.registry.entities_with_components(Position, Velocity):
            entity = await entity_ref.resolve()
            position = await entity.get_component(Position)
            velocity = await entity.get_component(Velocity)
            speed = (velocity.vx**2 + velocity.vy**2) ** 0.5
            if speed > self.max_speed:
                velocity.vx = velocity.vx / speed * self.max_speed
                velocity.vy = velocity.vy / speed * self.max_speed
            position.x += velocity.vx
            position.y += velocity.vy
            await entity.event_bus.emit(POSITION_UPDATED_EVENT_TYPE, position)


class VisionSystem(SpatialSystem):
    """
    System for detecting entities within the vision range of other entities.

    Methods:
        update: Detects entities within the vision range and emits ENTITY_SEEN_EVENT_TYPE events.
    """

    async def update(self):
        """
        Detects entities within the vision range of entities with Vision and Position components.
        Emits an ENTITY_SEEN_EVENT_TYPE event for each detected entity.
        """
        async for entity_ref in self.registry.entities_with_components(Vision, Position):
            entity = await entity_ref.resolve()
            vision = await entity.get_component(Vision)
            position = await entity.get_component(Position)
            async for other_entity_ref in self.registry.entities_within_distance(position, vision.max_range, Visible):
                if other_entity_ref.entity_id != entity.id:
                    other_entity = await other_entity_ref.resolve()
                    other_position = await other_entity.get_component(Position)
                    other_velocity = await other_entity.get_component(Velocity)
                    event = EntitySeenEvent(
                        entity_ref=other_entity_ref, position=other_position, velocity=other_velocity
                    )
                    await entity.event_bus.emit(ENTITY_SEEN_EVENT_TYPE, event)


class AudioSystem(SpatialSystem):
    """
    System for handling sound events and propagating them to entities with hearing capabilities.

    Methods:
        update: Processes sound events and emits SOUND_HEARD_EVENT_TYPE and SOUND_CREATED_EVENT_TYPE events.
    """

    async def update(self):
        """
        Processes sound events for entities with Hearing and Audible components.
        Emits SOUND_HEARD_EVENT_TYPE events for entities that hear sounds.
        Emits SOUND_CREATED_EVENT_TYPE events for entities that create sounds.
        """
        async for entity_ref in self.registry.entities_with_components(Hearing):
            entity = await entity_ref.resolve()
            hearing = await entity.get_component(Hearing)
            sound_queue = hearing.retrieve_queue(clear=True)
            for sound_event in sound_queue:
                await entity.event_bus.emit(SOUND_HEARD_EVENT_TYPE, sound_event)

        async for entity_ref in self.registry.entities_with_components(Audible, Position):
            entity = await entity_ref.resolve()
            audio = await entity.get_component(Audible)
            position = await entity.get_component(Position)
            sound_queue = audio.retrieve_queue(clear=True)
            for sound_event in sound_queue:
                await entity.event_bus.emit(SOUND_CREATED_EVENT_TYPE, sound_event)
                async for other_entity_ref in self.registry.entities_within_distance(position, audio.volume, Hearing):
                    if other_entity_ref.entity_id != entity.id:
                        other_entity = await other_entity_ref.resolve()
                        other_hearing = await other_entity.get_component(Hearing)
                        other_hearing.queue_sound(sound_event)


class LocationSystem(SpatialSystem):
    async def update(self):
        async for area_entity_ref in self.registry.entities_with_components(Area):
            area_entity: Entity = await area_entity_ref.resolve()
            area: Area = await area_entity.get_component(Area)

            existing_entity_refs: set[EntityRef] = area._entities
            _updated_entity_refs: set[EntityRef] = set()
            async for entity_ref in self.registry.entities_within_area(area):
                _updated_entity_refs.add(entity_ref)
                if entity_ref not in existing_entity_refs:
                    entity = await entity_ref.resolve()
                    try:
                        await entity.remove_component(Located)
                    except UnknownComponentError:
                        pass

                    await entity.add_component(Located(area_entity_ref=area_entity_ref))
                    event = AreaEvent(entity_ref=entity_ref, area_entity_ref=area_entity_ref)
                    await entity.event_bus.emit(AREA_ENTERED_EVENT_TYPE, event)
                    await area_entity.event_bus.emit(AREA_ENTERED_EVENT_TYPE, event)

            old_refs = existing_entity_refs - _updated_entity_refs
            for entity_ref in old_refs:
                entity = await entity_ref.resolve()
                event = AreaEvent(entity_ref=entity_ref, area_entity_ref=area_entity_ref)
                await self.registry.remove_component_from_entity(entity.id, Located)
                await entity.event_bus.emit(AREA_EXITED_EVENT_TYPE, event)
                await area_entity.event_bus.emit(AREA_EXITED_EVENT_TYPE, event)

            area._entities = _updated_entity_refs
