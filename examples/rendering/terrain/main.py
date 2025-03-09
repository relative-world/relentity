import asyncio
from pathlib import Path

import pygame

from relentity.core import Entity
from relentity.spatial import Position, Velocity, SpatialRegistry, MovementSystem
from relentity.rendering.components import RenderLayer, AnimatedSprite
from relentity.rendering.systems import RenderSystem
from examples.rendering.terrain.components import PlayerControlled
from examples.rendering.terrain.systems import InputSystem, TerrainSystem


async def main():
    # Initialize registry and systems
    registry = SpatialRegistry()

    # Create systems
    render_system = RenderSystem(registry, width=1200, height=800, title="Chunked Terrain Demo")
    movement_system = MovementSystem(registry, max_speed=200.0)
    input_system = InputSystem(registry)
    terrain_system = TerrainSystem(
        registry,
        width=1200,
        height=800,
        tile_size=50,
        chunk_size=8,  # 8x8 tiles per chunk
    )

    base_dir = Path(__file__).parent
    assets_dir = base_dir / "assets"

    # Initialize systems
    await render_system.initialize()
    await terrain_system.initialize()

    # Create player entity
    player = Entity(registry)
    await player.add_component(Position(x=0, y=0))
    await player.add_component(Velocity(vx=0, vy=0))
    await player.add_component(PlayerControlled(speed=200.0))
    await player.add_component(
        AnimatedSprite(
            animations={
                "idle": [assets_dir / "player.idle.0.png"],
                "walking": [assets_dir / f"player.walk.{i}.png" for i in range(12)],
            },
            current_state="idle",
            width=60,
            height=60,
            frame_duration=0.05,
            velocity_facing=True,  # Enable velocity facing
            base_rotation=0.0,  # Adjust if needed based on sprite orientation
        )
    )
    await player.add_component(RenderLayer(layer=10))  # Above terrain

    # Main game loop
    last_time = pygame.time.get_ticks()

    try:
        while render_system.running:
            # Process events to handle window closing
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    render_system.running = False

            # Calculate delta time
            current_time = pygame.time.get_ticks()
            delta_time = (current_time - last_time) / 1000.0
            last_time = current_time

            # Update systems
            await input_system.update(delta_time)
            await movement_system.update(delta_time)
            await terrain_system.update(delta_time)

            # Update camera position to follow player
            player_entity = await player.entity_ref.resolve()
            player_pos = await player_entity.get_component(Position)
            render_system.camera_x = player_pos.x
            render_system.camera_y = player_pos.y

            # Render
            await render_system.update(delta_time)

            # Small delay to prevent CPU maxing
            await asyncio.sleep(0.0)
    finally:
        await render_system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
