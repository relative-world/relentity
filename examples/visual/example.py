import asyncio
import random

import pygame

from relentity.core import Entity, Identity
from relentity.spatial import SpatialRegistry
from relentity.spatial.components import Position, Velocity
from relentity.spatial.systems import MovementSystem
from relentity.spatial.physics.systems import CollisionSystem
from relentity.spatial.physics.components import ShapeBody, ShapeType as BodyShapeType
from relentity.visual.components import RenderableShape, RenderableColor, ShapeType, RenderLayer
from relentity.visual.systems import RenderSystem


async def main():
    # Create registry and systems
    registry = SpatialRegistry()

    # Create systems
    movement_system = MovementSystem(registry, max_speed=300)
    render_system = RenderSystem(registry, width=800, height=800, title="Bouncing Balls Simulation")
    collision_system = CollisionSystem(registry)

    # Initialize renderer
    await render_system.initialize()

    # Create entities
    colors = [
        (255, 0, 0),  # Red
        (0, 255, 0),  # Green
        (0, 0, 255),  # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
    ]

    # Create 250 random entities
    for i in range(250):
        color = random.choice(colors)
        size = random.randint(5, 15)

        Entity[
            Identity(name=f"Ball-{i}", description="A ball"),
            Position(x=random.uniform(-300, 300), y=random.uniform(-300, 300)),
            Velocity(vx=random.uniform(-200, 200), vy=random.uniform(-200, 200)),
            ShapeBody(
                shape_type=BodyShapeType.CIRCLE,
                radius=size,
            ),
            RenderableShape(shape_type=ShapeType.CIRCLE, radius=size),
            RenderableColor(r=color[0], g=color[1], b=color[2]),
            RenderLayer(layer=0),
        ](registry)

    # Add boundary walls
    boundary_size = 400

    # Create the game loop
    last_time = pygame.time.get_ticks()

    try:
        while render_system.running:
            # Calculate delta time
            current_time = pygame.time.get_ticks()
            delta_time = (current_time - last_time) / 1000.0  # Convert to seconds
            last_time = current_time

            # Simple wall boundaries - reverse velocity when entity hits boundary
            async for entity_ref in registry.entities_with_components(Position, Velocity):
                entity = await entity_ref.resolve()
                pos = await entity.get_component(Position)
                vel = await entity.get_component(Velocity)

                if abs(pos.x) > boundary_size:
                    vel.vx = -vel.vx
                    pos.x = boundary_size if pos.x > 0 else -boundary_size

                if abs(pos.y) > boundary_size:
                    vel.vy = -vel.vy
                    pos.y = boundary_size if pos.y > 0 else -boundary_size

            # Update systems
            await collision_system.update(delta_time)
            await movement_system.update(delta_time)
            await render_system.update(delta_time)

    finally:
        await render_system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
