import asyncio
import json
import logging
import random
import time
from pathlib import Path

import pygame
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
from relentity.core import Entity, Identity, System
from relentity.core.entities import attach_components_sync
from relentity.spatial import (
    ENTITY_SEEN_EVENT_TYPE,
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
)
from relentity.spatial.sensory import VisionSystem, AudioSystem
from relentity.tasks import Task, TaskedEntity
from relentity.visual.components import RenderableShape, RenderableColor, RenderLayer, ShapeType, SpeechBubble
from relentity.visual.systems import RenderSystem

# Configure logging
logger = logging.getLogger("")
logger.setLevel(logging.WARN)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)


class MovementTask(Task):
    task: str = "moving to coordinates"
    target_x: float
    target_y: float
    speed: float = 50.0
    proximity_threshold: float = 5.0
    remaining_cycles: int = 100  # Will be completed when reaching target


class AIMovementController(ToolEnabledComponent):
    @tool
    async def stop_movement(self, actor):
        velocity = await actor.get_component(Velocity)
        if velocity:
            velocity.vx = 0
            velocity.vy = 0

    @tool
    async def go_to_coordinates(self, actor, x: float, y: float) -> str:
        """Move to the specified coordinates"""
        # Create and assign a movement task
        movement_task = MovementTask(target_x=x, target_y=y)
        await actor.set_task(movement_task)
        return f"Moving to coordinates ({x}, {y})"


class MovementTaskSystem(System):
    async def update(self, delta_time: float = 0) -> None:
        async for entity_ref in self.registry.entities_with_components(MovementTask, Position, Velocity):
            entity = await entity_ref.resolve()
            task = await entity.get_component(MovementTask)
            position = await entity.get_component(Position)
            velocity = await entity.get_component(Velocity)

            # Calculate direction to target
            dx = task.target_x - position.x
            dy = task.target_y - position.y
            distance = (dx**2 + dy**2) ** 0.5

            # Check if we've reached the target
            if distance <= task.proximity_threshold:
                # Stop movement
                velocity.vx = 0
                velocity.vy = 0
                # Complete the task
                task.remaining_cycles = 0
            else:
                # Update velocity toward target
                if distance > 0:
                    velocity.vx = task.speed * dx / distance
                    velocity.vy = task.speed * dy / distance


class Actor(TaskedEntity):
    def __init__(
        self,
        registry,
        name,
        description,
        width,
        color,
        *args,
        location=None,
        private_info=None,
        model="qwen2.5:14b",
        **kwargs,
    ):
        super().__init__(registry, *args, **kwargs)
        location = location or (random.randint(-200, 200), random.randint(-100, 100))
        components = [
            Identity(name=name, description=description),
            Position(x=location[0], y=location[1]),
            Velocity(vx=0, vy=0),
            TextPromptComponent(text=private_info) if private_info else None,
            AIMovementController(),
            Vision(max_range=1000),
            Visible(description=f"{name} - {description}"),
            Audible(volume=1000),
            Hearing(volume=1000),
            AIDriven(model=model, update_interval=1),
            RenderableShape(shape_type=ShapeType.CIRCLE, radius=width // 2),
            RenderableColor(r=color[0], g=color[1], b=color[2]),
            RenderLayer(layer=1),
            SpeechBubble(text=f"{name} - {description}", duration=10.0, start_time=time.time()),
        ]
        for component in components:
            if component:
                self.add_component_sync(component)

        self.event_bus.register_handler(AI_RESPONSE_EVENT_TYPE, self.on_ai_response)
        self.event_bus.register_handler(ENTITY_SEEN_EVENT_TYPE, self.on_entity_seen)
        self.event_bus.register_handler(SOUND_HEARD_EVENT_TYPE, self.on_sound_heard_event)
        self.event_bus.register_handler(SOUND_CREATED_EVENT_TYPE, self.on_sound_created_event)

    async def on_entity_seen(self, event):
        if event.entity_ref.entity_id is self.id:
            return
        ai_driven = await self.get_component(AIDriven)
        await ai_driven.add_event_for_consideration(ENTITY_SEEN_EVENT_TYPE, event, hash_key=event.entity_ref.entity_id)

    async def on_ai_response(self, response):
        audio = await self.get_component(Audible)
        sound_event = SoundEvent(self.entity_ref, "speech", response.text)
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
        # Add speech bubble component
        speech_bubble = SpeechBubble(text=sound_event.sound, duration=10.0, start_time=time.time())
        await self.add_component(speech_bubble)
        await ai_driven.add_event_for_consideration(SOUND_CREATED_EVENT_TYPE, sound_event)


class Ball(Entity):
    def __init__(self, registry, *args, **kwargs):
        super().__init__(registry, *args, **kwargs)
        attach_components_sync(
            self,
            Identity(name="a ball", description="A ball"),
            Position(x=0, y=1),
            Visible(description="A large red kickball, it's well inflated and says 'Spalding' on the side."),
            Hearing(),
        )
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
        location = entity_data.get("location")
        print(location)

        entity = Actor(
            registry,
            entity_data["name"],
            entity_data["description"],
            entity_data["width"],
            entity_data["color"],
            location=location,
        )

    elif entity_type == "Ball":
        entity = Ball(registry)
    else:
        entity = Entity(registry)

        await entity.add_component(
            RenderableShape(
                shape_type=ShapeType.RECTANGLE,
                radius=entity_data["width"],
                width=entity_data["width"],
                height=entity_data["width"],
            )
        )
        color = entity_data["color"]
        await entity.add_component(RenderableColor(r=color[0], g=color[1], b=color[2]))
        await entity.add_component(RenderLayer(layer=0))

    for component_name, component_data in components.items():
        component_class = globals()[component_name]
        await entity.add_component(component_class(**component_data))

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

    # Create systems
    movement_system = MovementSystem(registry, max_speed=50)
    render_system = RenderSystem(registry, width=1200, height=1200, title="Dave & Bill")
    ai_system = AIDrivenSystem(registry)
    vision_system = VisionSystem(registry)
    audio_system = AudioSystem(registry)
    movement_task_system = MovementTaskSystem(registry)

    # Initialize all systems
    await render_system.initialize()

    # Game loop code remains the same
    last_time = pygame.time.get_ticks()

    try:
        while render_system.running:
            # Calculate delta time
            current_time = pygame.time.get_ticks()
            delta_time = (current_time - last_time) / 1000.0
            last_time = current_time

            # Update systems
            await movement_system.update(delta_time)
            await vision_system.update(delta_time)
            await audio_system.update(delta_time)
            await ai_system.update(delta_time)
            await render_system.update(delta_time)
            await movement_task_system.update(delta_time)

    finally:
        await render_system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
