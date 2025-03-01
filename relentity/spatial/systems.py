from relentity.core.systems import System
from .components import Position, Velocity, Vision
from .events import EntitySeenEvent, ENTITY_SEEN_EVENT_TYPE, POSITION_UPDATED_EVENT_TYPE


class MovementSystem(System):
    max_speed = 10

    async def update(self):
        async for entity in self.registry.entities_with_components(Position, Velocity):
            position = await entity.get_component(Position)
            velocity = await entity.get_component(Velocity)
            speed = (velocity.vx ** 2 + velocity.vy ** 2) ** 0.5
            if speed > self.max_speed:
                velocity.vx = velocity.vx / speed * self.max_speed
                velocity.vy = velocity.vy / speed * self.max_speed
            position.x += velocity.vx
            position.y += velocity.vy
            await entity.event_bus.emit(POSITION_UPDATED_EVENT_TYPE, position)


class VisionSystem(System):
    async def update(self):
        async for entity in self.registry.entities_with_components(Vision, Position):
            vision = await entity.get_component(Vision)
            position = await entity.get_component(Position)
            async for other_entity in self.registry.entities_within_distance(position, vision.max_range, Position):
                if other_entity != entity:
                    other_position = await other_entity.get_component(Position)
                    event = EntitySeenEvent(entity=other_entity, position=other_position)
                    await entity.event_bus.emit(ENTITY_SEEN_EVENT_TYPE, event)
