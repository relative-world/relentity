import math
import random

import pygame

from relentity.core import System, Entity
from relentity.rendering.components import AnimatedSprite, RenderableShape, ShapeType, RenderableColor, RenderLayer
from relentity.spatial import Velocity, Position
from examples.rendering.terrain.components import PlayerControlled, TerrainChunk


class InputSystem(System):
    """System to handle keyboard input for player control"""

    async def update(self, delta_time: float = 0) -> None:
        keys = pygame.key.get_pressed()

        async for entity_ref in self.registry.entities_with_components(PlayerControlled, Velocity):
            entity = await entity_ref.resolve()
            player = await entity.get_component(PlayerControlled)
            velocity = await entity.get_component(Velocity)

            # Reset velocity
            velocity.vx = 0
            velocity.vy = 0

            # Update velocity based on key presses
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                velocity.vy = -player.speed
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                velocity.vy = player.speed
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                velocity.vx = -player.speed
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                velocity.vx = player.speed

            # Update animation state based on movement
            animated_sprite = await entity.get_component(AnimatedSprite)
            if animated_sprite:
                # Check if player is moving
                is_moving = velocity.vx != 0 or velocity.vy != 0
                animated_sprite.current_state = "walking" if is_moving else "idle"

                # Update sprite direction
                if velocity.vx < 0:
                    animated_sprite.flip_x = True
                elif velocity.vx > 0:
                    animated_sprite.flip_x = False


class TerrainSystem(System):
    """System for managing terrain chunks"""

    def __init__(self, registry, width=800, height=600, tile_size=50, chunk_size=8):
        super().__init__(registry)
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.chunk_size = chunk_size  # Number of tiles per chunk dimension
        self.terrain_types = {
            "grass": (34, 139, 34),  # Forest green
            "water": (65, 105, 225),  # Royal blue
            "rock": (169, 169, 169),  # Dark gray
            "sand": (210, 180, 140),  # Tan
        }
        self.view_range = 3  # Chunks visible in each direction
        self.generated_chunks = {}  # (chunk_x, chunk_y) -> entity_id
        self.chunk_pixel_size = self.tile_size * self.chunk_size

        # For deterministic terrain generation
        self.seed = random.randint(0, 10000)
        random.seed(self.seed)

    async def initialize(self):
        """Generate initial terrain chunks"""
        # Generate terrain in view range around origin
        for x in range(-self.view_range, self.view_range + 1):
            for y in range(-self.view_range, self.view_range + 1):
                await self.create_chunk_at(x, y)

    async def update(self, delta_time: float = 0) -> None:
        """Update terrain based on player position"""
        # Find player position
        player_pos = None
        async for entity_ref in self.registry.entities_with_components(PlayerControlled, Position):
            entity = await entity_ref.resolve()
            player_pos = await entity.get_component(Position)
            break

        if not player_pos:
            return

        # Calculate which chunk the player is in
        chunk_x = int(player_pos.x / self.chunk_pixel_size)
        chunk_y = int(player_pos.y / self.chunk_pixel_size)

        # Generate chunks as needed
        for x in range(chunk_x - self.view_range, chunk_x + self.view_range + 1):
            for y in range(chunk_y - self.view_range, chunk_y + self.view_range + 1):
                if (x, y) not in self.generated_chunks:
                    await self.create_chunk_at(x, y)

        # Clean up far away chunks
        chunks_to_remove = []
        for pos, entity_id in list(self.generated_chunks.items()):
            x, y = pos
            if abs(x - chunk_x) > self.view_range + 1 or abs(y - chunk_y) > self.view_range + 1:
                chunks_to_remove.append((pos, entity_id))

        # Remove chunks that are too far away
        for pos, entity_id in chunks_to_remove:
            del self.generated_chunks[pos]
            try:
                await self.registry.remove_entity(entity_id)
            except Exception as e:
                print(f"Warning: Could not remove entity {entity_id}: {e}")

    def get_terrain_type(self, global_x, global_y):
        """Deterministic terrain type based on position"""
        # Use a more varied formula for terrain generation
        value = (
            global_x * 0.5 + global_y * 0.7 + math.sin(global_x * 0.2) * 30 + math.cos(global_y * 0.2) * 30 + self.seed
        ) % 100

        if value < 25:
            return "water"
        elif value < 60:
            return "grass"
        elif value < 85:
            return "sand"
        else:
            return "rock"

    async def create_chunk_at(self, chunk_x, chunk_y):
        """Create a terrain chunk at the specified grid position"""
        # Calculate world position
        world_x = chunk_x * self.chunk_pixel_size
        world_y = chunk_y * self.chunk_pixel_size

        # Create the chunk entity
        chunk_entity = Entity(self.registry)
        await chunk_entity.add_component(Position(x=world_x, y=world_y))
        await chunk_entity.add_component(TerrainChunk(chunk_x=chunk_x, chunk_y=chunk_y))
        await chunk_entity.add_component(
            RenderableShape(shape_type=ShapeType.RECTANGLE, width=self.chunk_pixel_size, height=self.chunk_pixel_size)
        )

        # Determine the predominant terrain type for this chunk
        terrain_type = self.get_terrain_type(chunk_x, chunk_y)
        color = self.terrain_types[terrain_type]
        await chunk_entity.add_component(RenderableColor(r=color[0], g=color[1], b=color[2]))
        await chunk_entity.add_component(RenderLayer(layer=0))

        # Store reference to the generated chunk
        self.generated_chunks[(chunk_x, chunk_y)] = chunk_entity.id
