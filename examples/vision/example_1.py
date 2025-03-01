import asyncio
import random

from relentity.ai.components import AIDriven
from relentity.core import Entity, Position, Registry
from relentity.core.components import Velocity, Component
from relentity.spatial.systems import MovementSystem, VisionSystem
from relentity.spatial.components import Vision
from relentity.spatial.events import ENTITY_SEEN_EVENT_TYPE, EntitySeenEvent


class Named(Component):
    name: str


class Actor(Entity):

    def __init__(self, registry, name, *args, **kwargs):
        super().__init__(registry, *args, **kwargs)
        self.add_component_sync(Named(name=name))
        self.add_component_sync(Position(x=random.randint(-5, 5), y=random.randint(-5, 5)))
        self.add_component_sync(Velocity(vx=random.randint(-1, 1), vy=random.randint(-1, 1)))
        self.add_component_sync(Vision(max_range=10))
        self.add_component_sync(AIDriven(model="qwen2.5:14b"))
        self.event_bus.register_handler(ENTITY_SEEN_EVENT_TYPE, self.on_entity_seen)

    async def on_entity_seen(self, event: EntitySeenEvent):
        name = (await self.get_component(Named)).name
        print(f"{name}:: Entity {event.entity} seen at position {event.position}")


async def main():
    registry = Registry()

    actors = [
        Actor(registry, "Alice"),
        Actor(registry, "Bob"),
        Actor(registry, "Charlie")
    ]

    movement_system = MovementSystem(registry=registry)
    vision_system = VisionSystem(registry=registry)

    for _ in range(20):
        await vision_system.update()
        await movement_system.update()


if __name__ == "__main__":
    asyncio.run(main())
