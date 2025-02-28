from itertools import chain

from aiostream import stream

from relentity.components.position import Position
from relentity.components.velocity import Velocity, TooledVelocity
from relentity.systems.base import System


class MovementSystem(System):
    async def update(self):
        async for entity in self.registry.entities_with_components(Position, Velocity):
            position = await entity.get_component(Position)
            velocity = await entity.get_component(Velocity)
            position.x += velocity.vx
            position.y += velocity.vy
            await entity.event_bus.emit("position_updated", position)
