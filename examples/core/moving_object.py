from relentity.core import Entity, Registry
from relentity.spatial.systems import MovementSystem
from relentity.spatial.components import Velocity, Position


async def on_position_updated(data):
    print(f"Position updated: {data.x}, {data.y}")


async def main():
    registry = Registry()

    Bullet = Entity[
        Velocity(vx=1, vy=1),
        Position(x=0, y=0),
    ]

    bullet = Bullet(registry=registry)
    bullet.event_bus.register_handler("position_updated", on_position_updated)

    movement_system = MovementSystem(registry=registry)
    for _ in range(20):
        await asyncio.gather(
            movement_system.update(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
