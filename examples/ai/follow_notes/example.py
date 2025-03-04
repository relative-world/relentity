import asyncio
import json
import logging
import random
import time
from pathlib import Path

import pygame
from pythonjsonlogger.json import JsonFormatter

from relentity.ai import (
    TextPromptComponent,
    AI_RESPONSE_EVENT_TYPE,
    AIDrivenSystem,
)
from relentity.ai.components import AIDriven, ToolEnabledComponent
from relentity.ai.pydantic_ollama.tools import tool
from relentity.ai.utils import pretty_name_entity, pretty_print_event
from relentity.core import Component, Entity, Identity, System
from relentity.core.entities import attach_components_sync
from relentity.spatial import Position, Area
from relentity.spatial import (
    Velocity,
    SpatialRegistry,
    MovementSystem,
)
from relentity.spatial.events import AREA_ENTERED_EVENT_TYPE, AREA_EXITED_EVENT_TYPE, AreaEvent
from relentity.spatial.events import (
    ENTITY_SEEN_EVENT_TYPE,
    SOUND_HEARD_EVENT_TYPE,
    SOUND_CREATED_EVENT_TYPE,
    SoundEvent,
)
from relentity.spatial.sensory.components import Visible, Audible
from relentity.spatial.sensory.components import Vision, Hearing
from relentity.spatial.sensory.systems import VisionSystem, AudioSystem
from relentity.spatial.systems import LocationSystem
from relentity.tasks import Task, TaskedEntity
from relentity.visual.components import RenderableColor, RenderableShape, ShapeType, RenderLayer
from relentity.visual.components import SpeechBubble
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

            if not task:
                continue

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


class FireTools(ToolEnabledComponent):
    @tool
    async def light_fire(self, actor) -> str:
        """Light the fire in the fire pit"""
        fire_pit = await self._fire_pit_ref.resolve()
        fire_pit_component = await fire_pit.get_component(FirePit)

        if fire_pit_component.is_lit:
            return "The fire is already lit."

        fire_pit_component.is_lit = True

        # Update visual appearance
        visual = await fire_pit.get_component(RenderableColor)
        visual.r, visual.g, visual.b = 255, 100, 0  # Orange-red glow

        # Create sound effect
        audible = await fire_pit.get_component(Audible)
        from relentity.spatial.events import SoundEvent

        audible.queue_sound(SoundEvent(fire_pit.entity_ref, "ambient", "The fire crackles as it burns."))

        return "You've lit the fire. The flames crackle and provide warmth."

    @tool
    async def put_out_fire(self, actor) -> str:
        """Put out the fire in the fire pit"""
        fire_pit = await self._fire_pit_ref.resolve()
        fire_pit_component = await fire_pit.get_component(FirePit)

        if not fire_pit_component.is_lit:
            return "The fire is already out."

        fire_pit_component.is_lit = False

        # Update visual appearance
        visual = await fire_pit.get_component(RenderableColor)
        visual.r, visual.g, visual.b = 50, 50, 50  # Dark gray

        # Create sound effect
        audible = await fire_pit.get_component(Audible)
        from relentity.spatial.events import SoundEvent

        audible.queue_sound(SoundEvent(fire_pit.entity_ref, "ambient", "The fire hisses as it goes out."))

        return "You've extinguished the fire."


class FirePit(Component):
    """Component representing a fire pit that can be lit or extinguished"""

    is_lit: bool = False

    async def handle_area_entered(self, event: AreaEvent):
        entity = await event.entity_ref.resolve()
        print("Fire pit area entered by", entity)

        # Check if the entity is AI-driven
        ai_driven = await entity.get_component(AIDriven)
        if ai_driven:
            # Add fire tools to the entity
            fire_tools = FireTools()
            fire_tools._fire_pit_ref = event.area_entity_ref
            await entity.add_component(fire_tools)

            # Update the AI's extra_tools dictionary
            ai_driven.extra_tools.update(fire_tools._tools)

            # Notify the AI
            status = "lit" if self.is_lit else "unlit"
            await ai_driven.add_event_for_consideration(
                "environment.feature", f"You've entered a fire pit area. The fire is currently {status}."
            )

    async def handle_area_exited(self, event: AreaEvent):
        entity = await event.entity_ref.resolve()
        print("Fire pit area entered by", entity)

        # Check if the entity is AI-driven
        ai_driven = await entity.get_component(AIDriven)
        if ai_driven:
            fire_tools = await entity.get_component(FireTools)

            # Remove the tools from AI's extra_tools
            for tool_name in fire_tools._tools:
                ai_driven.extra_tools.pop(tool_name, None)

            await entity.remove_component(FireTools)

            await ai_driven.add_event_for_consideration(
                "environment.feature", "You've left the fire pit area and can no longer interact with the fire."
            )


async def create_fire_pit(registry, x=0, y=0, radius=50):
    """Create a fire pit entity that provides fire tools to AI entities"""

    buffered_radius = radius + 50
    fire_pit = Entity[
        Identity(
            name="Fire Pit",
            description="A well stocked firepit, ready to make a fire.  A great place to make camp.  Wood and fire starting materials are already here.",
        ),
        Position(x=x, y=y),
        Area(
            center_point=(x, y),
            geometry=[
                (x - buffered_radius, y - buffered_radius),
                (x, y + buffered_radius),
                (x + buffered_radius, y - buffered_radius),
                (x, y - buffered_radius),
            ],
        ),
        Visible(
            description="A well stocked firepit, ready to make a fire.  A great place to make camp.  Wood and fire starting materials are already here."
        ),
        Audible(volume=20),
        RenderableShape(shape_type=ShapeType.RECTANGLE, radius=radius, width=radius, height=radius),
        RenderableColor(r=50, g=50, b=50),  # Start with gray (unlit)
        RenderLayer(layer=0),
        FirePit(),
    ](registry)

    # Register event handlers
    fire_pit_component = await fire_pit.get_component(FirePit)
    fire_pit.event_bus.register_handler(AREA_ENTERED_EVENT_TYPE, fire_pit_component.handle_area_entered)
    fire_pit.event_bus.register_handler(AREA_EXITED_EVENT_TYPE, fire_pit_component.handle_area_exited)

    return fire_pit


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
    location_system = LocationSystem(registry)

    # Initialize all systems
    await render_system.initialize()

    # Game loop code remains the same
    last_time = pygame.time.get_ticks()

    await create_fire_pit(registry, x=100, y=100)

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
            await location_system.update(delta_time)

    finally:
        await render_system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
