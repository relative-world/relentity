from relentity.ai.components import AIDriven, ToolEnabledComponent
from relentity.ai.events import AI_RESPONSE_EVENT_TYPE
from relentity.ai.pydantic_ollama.tools import tool
from relentity.ai.systems import AIDrivenSystem
from relentity.core.components import Identity
from relentity.core.entities import Entity
from relentity.spatial import Position, Velocity, Vision, Visible, SpatialRegistry, ENTITY_SEEN_EVENT_TYPE, \
    POSITION_UPDATED_EVENT_TYPE
from relentity.spatial.systems import MovementSystem, VisionSystem


class AIMovementController(ToolEnabledComponent):

    @tool
    async def set_velocity(self, actor, vx: float, vy: float):
        velocity = await actor.get_component(Velocity)
        if velocity:
            velocity.vx = float(vx)
            velocity.vy = float(vy)

    @tool
    async def stop_movement(self, actor):
        velocity = await actor.get_component(Velocity)
        if velocity:
            velocity.vx = 0
            velocity.vy = 0


async def pretty_name_entity(entity):
    ident = await entity.get_component(Identity)
    if ident:
        return ident.name
    else:
        return repr(entity)


async def pretty_print_event(event_type: str, data):
    if event_type == "position_updated":
        return f"Position updated to ({data.x}, {data.y})"
    elif event_type == "entity_seen":
        entity_name = await pretty_name_entity(data.entity)
        description = (await data.entity.get_component(Visible)).description
        position = data.position
        return f"You see {entity_name} at ({position.x}, {position.y}) - ({description})"
    elif event_type == "task.progress":
        return f"Task progress: {data.progress}%"
    elif event_type == "task.complete":
        return f"Task complete: {data.task_name}"
    elif event_type == "task.abandoned":
        return f"Task abandoned: {data.task_name}"
    else:
        return f"Event type: {event_type} with data: {data}"


class Actor(Entity):
    _ai_event_queue = []
    _ai_event_history = []

    def __init__(self, registry, name, description, *args, **kwargs):
        super().__init__(registry, *args, **kwargs)
        self.add_component_sync(Identity(name=name, description=description))
        self.add_component_sync(Position(x=0, y=0))
        self.add_component_sync(Velocity(vx=1, vy=1, max_speed=20))
        self.add_component_sync(AIMovementController())
        self.add_component_sync(Vision(max_range=10))
        self.add_component_sync(AIDriven(model="qwen2.5:14b", update_interval=1))
        self.event_bus.register_handler(AI_RESPONSE_EVENT_TYPE, self.on_ai_response)
        self.event_bus.register_handler(ENTITY_SEEN_EVENT_TYPE, self.on_entity_seen)

    async def render_prompt(self):
        _ai_event_queue, self._ai_event_queue = self._ai_event_queue, []
        self._ai_event_history.extend(_ai_event_queue)
        return "\n".join(_ai_event_queue)

    async def render_system_prompt(self):
        return "Previous events:\n" + "\n".join(list(set(self._ai_event_history))[-100::][::-1])

    async def on_entity_seen(self, event):
        if event.entity is self:
            return
        event_msg = await pretty_print_event(ENTITY_SEEN_EVENT_TYPE, event)
        self._ai_event_queue.append(event_msg)

    async def on_ai_response(self, response):
        msg = f"You said: {response.text}"
        print(msg)
        self._ai_event_queue.append(msg)


async def on_position_updated(event):
    event_msg = await pretty_print_event("position_updated", event)
    print(event_msg)


async def main():
    registry = SpatialRegistry()

    Ball = Entity[
        Identity(name="a ball", description="A ball"),
        Position(x=0, y=1),
        Visible(description="A large red kickball, it's well inflated and says 'Spalding' on the side."),
    ]

    Entity[
        Identity(name="a tree", description="A tree"),
        Position(x=205, y=98),
        Visible(description="A large oak tree, its branches are full of leaves."),
    ](registry)

    Entity[
        Identity(name="a flower", description="A flower"),
        Position(x=100, y=98),
        Visible(description="A small yellow flower, its petals are wilting."),
    ](registry)

    note_0 = Entity[
        Identity(name="a note", description="A note"),
        Position(x=2, y=0),
        Visible(
            description="A scrap of paper with some writing on it.  the writing says 'seek the next clue at (100, 100)."),
    ](registry)

    note_1 = Entity[
        Identity(name="a note", description="A note"),
        Position(x=100, y=100),
        Visible(description="The next clue awaits you at (200, 100)"),
    ](registry)

    note_2 = Entity[
        Identity(name="a note", description="A note"),
        Position(x=200, y=100),
        Visible(description="The final clue is at (300, 300)"),
    ](registry)

    note_3 = Entity[
        Identity(name="a note", description="A note"),
        Position(x=300, y=300),
        Visible(description="Oh no! I had to run to the store, but I left you a surprise at (0, 0)"),
    ](registry)

    actor = Actor(
        registry,
        "Dave",
        "A confused person that woke up in an endless field of grass in a virtual world.",
    )
    actor.event_bus.register_handler(POSITION_UPDATED_EVENT_TYPE, on_position_updated)
    ball = Ball(registry)

    movement_system = MovementSystem(registry)
    ai_system = AIDrivenSystem(registry)
    vision_system = VisionSystem(registry)

    for _ in range(100):
        await movement_system.update()
        await vision_system.update()
        await ai_system.update()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
