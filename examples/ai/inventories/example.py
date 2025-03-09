import asyncio
import json
import logging
from pathlib import Path

import pygame
from pythonjsonlogger.json import JsonFormatter

from examples.ai.inventories.entities.actor import Actor
from examples.ai.inventories.entities.firepit import create_fire_pit
from examples.ai.inventories.systems import MovementTaskSystem
from relentity.ai import AIDrivenSystem, AIDriven, TextPromptComponent, TextSystemPromptComponent
from relentity.core import Entity, Identity
from relentity.spatial import (
    SpatialRegistry,
    MovementSystem,
    Velocity,
    Position,
    Area,
    Located,
)
from relentity.spatial.physics.systems import CollisionSystem
from relentity.spatial.sound.systems import AudioSystem
from relentity.spatial.vision.systems import VisionSystem
from relentity.spatial.systems import LocationSystem
from relentity.rendering.components import RenderableColor, RenderableShape, ShapeType, RenderLayer
from relentity.rendering.systems import RenderSystem

# Configure logging
logger = logging.getLogger("")
logger.setLevel(logging.WARN)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)


def get_component_class_by_name(component_name):
    _classes = {
        "Identity": Identity,
        "Velocity": Velocity,
        "Position": Position,
        "Area": Area,
        "Located": Located,
        "RenderableColor": RenderableColor,
        "RenderableShape": RenderableShape,
        "RenderLayer": RenderLayer,
        "AIDriven": AIDriven,
        "TextPromptComponent": TextPromptComponent,
        "TextSystemPromptComponent": TextSystemPromptComponent,
    }
    return _classes[component_name]


async def create_entity(entity_data, registry):
    entity_type = entity_data["type"]
    components = entity_data.get("components", {})

    if entity_type == "Actor":
        location = entity_data.get("location")

        entity = Actor(
            registry,
            entity_data["name"],
            entity_data["description"],
            entity_data["width"],
            entity_data["color"],
            location=location,
        )
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
        component_class = get_component_class_by_name(component_name)
        await entity.add_component(component_class(**component_data))

    return entity


def get_world_data(world_filename):
    with open(Path(__file__).parent / world_filename) as f:
        config = f.read()
    return json.loads(config)


async def main():
    world_filename = "party.json"
    registry = SpatialRegistry()
    config_data = get_world_data(world_filename)

    for entity_data in config_data["entities"]:
        await create_entity(entity_data, registry)

    # Create systems
    movement_system = MovementSystem(registry, max_speed=50)
    render_system = RenderSystem(registry, width=1200, height=1200)
    ai_system = AIDrivenSystem(registry)
    vision_system = VisionSystem(registry)
    audio_system = AudioSystem(registry)
    movement_task_system = MovementTaskSystem(registry)
    location_system = LocationSystem(registry)
    collision_system = CollisionSystem(registry)

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
            await collision_system.update(delta_time)

    finally:
        await render_system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
