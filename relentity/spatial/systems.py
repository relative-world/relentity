from relentity.core.systems import System
from .events import SOUND_CREATED_EVENT_TYPE
from .registry import SpatialRegistry
from .components import Position, Velocity, Vision, Audible, Hearing, Visible
from .events import EntitySeenEvent, ENTITY_SEEN_EVENT_TYPE, POSITION_UPDATED_EVENT_TYPE, SOUND_HEARD_EVENT_TYPE


class SpatialSystem(System):
    def __init__(self, registry: SpatialRegistry):
        super().__init__(registry)
        self.registry = registry


class MovementSystem(SpatialSystem):
    max_speed = 30

    async def update(self):
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
    async def update(self):
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
    async def update(self):
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
