from relentity.core import Component
from relentity.core.entities import Entity
from relentity.core.registry import Registry


async def on_position_updated(data):
    print(f"Position updated: {data.x}, {data.y}")


class Identity(Component):
    name: str
    description: str


async def main():
    registry = Registry()

    NewPlayer = Entity[
        Identity(name="John Ward", description="Go to (10.0, 20.0) and wait there"),
        Position(x=0, y=0),
        Velocity(vx=1, vy=1),
        TooledVelocity(),
        AIAgentSystemPrompt(),
        AIAgent(model="qwen2.5:14b"),
    ]

    entity = NewPlayer(registry)
    entity.event_bus.register_handler("position_updated", on_position_updated)

    await (await kitchen.get_component(Location)).add_entity(entity)

    movement_system = MovementSystem(registry)
    ai_agent_system = AiAgentSystem(registry)

    for _ in range(20):
        await movement_system.update()
        await ai_agent_system.update()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
