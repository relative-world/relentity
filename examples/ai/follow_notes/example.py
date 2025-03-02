import asyncio
import json
import logging
import random
from pathlib import Path

from pythonjsonlogger.json import JsonFormatter

from relentity.ai import (
    AIDriven,
    ToolEnabledComponent,
    TextPromptComponent,
    AI_RESPONSE_EVENT_TYPE,
    tool,
    AIDrivenSystem,
)
from relentity.ai.utils import pretty_name_entity, pretty_print_event
from relentity.core import Entity, Identity
from relentity.spatial import (
    ENTITY_SEEN_EVENT_TYPE,
    POSITION_UPDATED_EVENT_TYPE,
    SoundEvent,
    SOUND_HEARD_EVENT_TYPE,
    SOUND_CREATED_EVENT_TYPE,
    Position,
    Velocity,
    Vision,
    Visible,
    Audible,
    Hearing,
    SpatialRegistry,
    MovementSystem,
    VisionSystem,
    AudioSystem,
)

# Configure logging
logger = logging.getLogger("")
logger.setLevel(logging.WARN)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)


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


class Actor(Entity):

    def __init__(self, registry, name, description, *args, private_info=None, model="qwen2.5:14b", **kwargs):
        super().__init__(registry, *args, **kwargs)
        self.add_component_sync(Identity(name=name, description=description))
        self.add_component_sync(Position(x=random.randint(-10, 10), y=random.randint(-10, 10)))
        self.add_component_sync(Velocity(vx=0, vy=0))

        if private_info:
            self.add_component_sync(TextPromptComponent(text=private_info))

        self.add_component_sync(AIMovementController())
        self.add_component_sync(Vision(max_range=1000))
        self.add_component_sync(Visible(description=f"{name} - {description}"))
        self.add_component_sync(Audible(volume=100))
        self.add_component_sync(Hearing(volume=100))
        self.add_component_sync(AIDriven(model=model, update_interval=1))

        self.event_bus.register_handler(AI_RESPONSE_EVENT_TYPE, self.on_ai_response)
        self.event_bus.register_handler(ENTITY_SEEN_EVENT_TYPE, self.on_entity_seen)
        self.event_bus.register_handler(SOUND_HEARD_EVENT_TYPE, self.on_sound_heard_event)
        self.event_bus.register_handler(SOUND_CREATED_EVENT_TYPE, self.on_sound_created_event)
        self.event_bus.register_handler(POSITION_UPDATED_EVENT_TYPE, self.on_position_updated)

    async def on_position_updated(self, event):
        name = await pretty_name_entity(self)
        print(f"{name} position updated - {event.x}, {event.y}")

    async def on_entity_seen(self, event):
        if event.entity is self:
            return
        ai_driven = await self.get_component(AIDriven)
        await ai_driven.add_event_for_consideration(ENTITY_SEEN_EVENT_TYPE, event, hash_key=id(event.entity))

    async def on_ai_response(self, response):
        audio = await self.get_component(Audible)
        sound_event = SoundEvent(self, "speech", response.text)
        audio.queue_sound(sound_event)

    async def on_sound_heard_event(self, sound_event):
        ai_driven = await self.get_component(AIDriven)
        pretty_msg = await pretty_print_event(SOUND_HEARD_EVENT_TYPE, sound_event)
        pretty_name = await pretty_name_entity(self)
        print(f"{pretty_name} :: {pretty_msg}")
        await ai_driven.add_event_for_consideration(SOUND_HEARD_EVENT_TYPE, sound_event)

    async def on_sound_created_event(self, sound_event):
        ai_driven = await self.get_component(AIDriven)
        pretty_msg = await pretty_print_event(SOUND_CREATED_EVENT_TYPE, sound_event)
        pretty_name = await pretty_name_entity(self)
        print(f"{pretty_name} :: {pretty_msg}")
        await ai_driven.add_event_for_consideration(SOUND_CREATED_EVENT_TYPE, sound_event)


class Ball(Entity):

    def __init__(self, registry, *args, **kwargs):
        super().__init__(registry, *args, **kwargs)
        self.add_component_sync(Identity(name="a ball", description="A ball"))
        self.add_component_sync(Position(x=0, y=1))
        self.add_component_sync(
            Visible(description="A large red kickball, it's well inflated and says 'Spalding' on the side.")
        )
        self.add_component_sync(Hearing())
        self.event_bus.register_handler(SOUND_HEARD_EVENT_TYPE, self.on_sound_heard_event)

    async def on_sound_heard_event(self, sound_event):
        if "the sun" in sound_event.sound.lower():
            Entity[
                Identity(name="a mysterious door", description="A mysterious door"),
                Position(x=10, y=0),
                Visible(description="A mysterious door"),
            ](self.registry)


async def create_entity(entity_data, registry):
    entity_type = entity_data["type"]
    components = entity_data["components"]

    if entity_type == "Actor":
        entity = Actor(registry, entity_data["name"], entity_data["description"])
    elif entity_type == "Ball":
        entity = Ball(registry)
    else:
        entity = Entity(registry)

    for component_name, component_data in components.items():
        component_class = globals()[component_name]
        entity.add_component_sync(component_class(**component_data))

    return entity


def get_world_data(world_filename):
    with open(Path(__file__).parent / world_filename) as f:
        config = f.read()
    return json.loads(config)


async def main():
    world_filename = "world.json"
    registry = SpatialRegistry()
    config_data = get_world_data(world_filename)

    for entity_data in config_data["entities"]:
        await create_entity(entity_data, registry)

    movement_system = MovementSystem(registry)
    ai_system = AIDrivenSystem(registry)
    vision_system = VisionSystem(registry)
    audio_system = AudioSystem(registry)

    for _ in range(100):
        await movement_system.update()
        await vision_system.update()
        await ai_system.update()
        await audio_system.update()


if __name__ == "__main__":
    asyncio.run(main())
