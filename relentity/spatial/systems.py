from relentity.core.systems import System
from .events import SOUND_CREATED_EVENT_TYPE
from .registry import SpatialRegistry
from .components import Position, Velocity, Vision, Audible, Hearing, Visible
from .events import EntitySeenEvent, ENTITY_SEEN_EVENT_TYPE, POSITION_UPDATED_EVENT_TYPE, SOUND_HEARD_EVENT_TYPE


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
        async for entity in self.registry.entities_with_components(Position, Velocity):
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
        async for entity in self.registry.entities_with_components(Vision, Position):
            vision = await entity.get_component(Vision)
            position = await entity.get_component(Position)
            async for other_entity in self.registry.entities_within_distance(position, vision.max_range, Visible):
                if other_entity != entity:
                    other_position = await other_entity.get_component(Position)
                    other_velocity = await other_entity.get_component(Velocity)
                    event = EntitySeenEvent(entity=other_entity, position=other_position, velocity=other_velocity)
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
        async for entity in self.registry.entities_with_components(Hearing):
            hearing = await entity.get_component(Hearing)
            sound_queue = hearing.retrieve_queue(clear=True)
            for sound_event in sound_queue:
                await entity.event_bus.emit(SOUND_HEARD_EVENT_TYPE, sound_event)

        async for entity in self.registry.entities_with_components(Audible, Position):
            audio = await entity.get_component(Audible)
            position = await entity.get_component(Position)
            sound_queue = audio.retrieve_queue(clear=True)
            for sound_event in sound_queue:
                await entity.event_bus.emit(SOUND_CREATED_EVENT_TYPE, sound_event)
                async for other_entity in self.registry.entities_within_distance(position, audio.volume, Hearing):
                    if other_entity != entity:
                        other_hearing = await other_entity.get_component(Hearing)
                        other_hearing.queue_sound(sound_event)
