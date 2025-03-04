from relentity.spatial import Position, Velocity
from relentity.spatial.events import (
    ENTITY_SEEN_EVENT_TYPE,
    EntitySeenEvent,
    SOUND_HEARD_EVENT_TYPE,
    SOUND_CREATED_EVENT_TYPE,
)
from relentity.spatial.sensory.components import Vision, Hearing, Audible, Visible
from relentity.spatial.systems import SpatialSystem


class VisionSystem(SpatialSystem):
    """
    System for detecting entities within the vision range of other entities.

    Methods:
        update: Detects entities within the vision range and emits ENTITY_SEEN_EVENT_TYPE events.
    """

    async def update(self, delta_time: float = 0) -> None:
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

    async def update(self, delta_time: float = 0) -> None:
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
