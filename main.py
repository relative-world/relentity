from relentity.components.ai_agents import AIAgent, AIAgentSystemPrompt
from relentity.components.identity import Identity
from relentity.components.position import Position
from relentity.components.velocity import TooledVelocity, Velocity
from relentity.entity import Entity
from relentity.registry import Registry
from relentity.systems.ai_agents import AiAgentSystem
from relentity.systems.movement import MovementSystem


async def on_position_updated(data):
    print(f"Position updated: {data.x}, {data.y}")


async def main():
    registry = Registry()

    NewPlayer = Entity[
        Identity(name="John Ward", description="GO to 10, 20 and wait there"),
        Position(x=0, y=0),
        Velocity(vx=1, vy=1),
        TooledVelocity(),
        AIAgentSystemPrompt(),
        AIAgent(model="qwen2.5:14b"),
    ]

    entity = NewPlayer(registry)
    entity.event_bus.register_handler("position_updated", on_position_updated)

    movement_system = MovementSystem(registry)
    ai_agent_system = AiAgentSystem(registry)

    for _ in range(10):
        await movement_system.update()
        await ai_agent_system.update()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
