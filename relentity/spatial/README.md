# relentity.spatial

## Overview

`relentity.spatial` extends the `relentity.core` framework to provide specialized components and systems for simulations with spatial awareness. This module enables:

- Position and movement tracking
- Vision and sight mechanics
- Sound propagation and hearing
- Spatial queries to find entities within specified distances

This extension maintains the core ECS architecture while adding functionality specific to spatially-situated simulations, games, and AI environments.

## Core Spatial Components

### Position

Tracks an entity's location in 2D space.

```python
from relentity.spatial.components import Position

# Create an entity at coordinates (10, 20)
entity = Entity[Position(x=10, y=20)](registry)
```

### Velocity

Defines an entity's movement speed and direction.

```python
from relentity.spatial.components import Velocity

# Create a moving entity
entity = Entity[
    Position(x=0, y=0),
    Velocity(vx=5, vy=2)  # Moving at 5 units/tick in X and 2 in Y
](registry)
```

### Vision

Enables entities to see other visible entities within a specified range.

```python
from relentity.spatial.components import Vision, Visible

# Entity that can see up to 100 units away
observer = Entity[Position(x=0, y=0), Vision(max_range=100)](registry)

# Entity that can be seen by others
target = Entity[Position(x=50, y=50), Visible()](registry)
```

### Audible & Hearing

Provides sound generation and reception capabilities.

```python
from relentity.spatial.components import Audible, Hearing

# Entity that can make sounds
speaker = Entity[Position(x=0, y=0), Audible(volume=50)](registry)

# Entity that can hear sounds
listener = Entity[Position(x=30, y=30), Hearing()](registry)

# Generate a sound
audio = await speaker.get_component(Audible)
audio.queue_sound(SoundEvent(speaker, "voice", "Hello!"))
```

## Spatial Registry

`SpatialRegistry` extends the core `Registry` with spatial query capabilities.

```python
from relentity.spatial.registry import SpatialRegistry

registry = SpatialRegistry()

# Find all entities with a Health component within 50 units of position
position = Position(x=10, y=10)
async for entity in registry.entities_within_distance(position, 50, Health):
    # Process nearby entities with Health component
    health = await entity.get_component(Health)
    # Do something with nearby entity...
```

## Spatial Systems

### MovementSystem

Updates entity positions based on their velocities, enforcing maximum speed limits.

```python
from relentity.spatial.systems import MovementSystem

# Create a movement system with custom max speed
movement_system = MovementSystem(registry)
movement_system.max_speed = 5  # Override default max speed
```

### VisionSystem

Generates events when entities "see" other visible entities within their vision range.

```python
from relentity.spatial.systems import VisionSystem

# Create a vision system
vision_system = VisionSystem(registry)

# Handle vision events
async def on_entity_seen(event):
    print(f"Entity seen at position ({event.position.x}, {event.position.y})")

entity.event_bus.register_handler(ENTITY_SEEN_EVENT_TYPE, on_entity_seen)
```

### AudioSystem

Manages sound propagation between entities with Audible and Hearing components.

```python
from relentity.spatial.systems import AudioSystem

# Create an audio system
audio_system = AudioSystem(registry)

# Handle sound events
async def on_sound_heard(sound_event):
    print(f"Heard sound: {sound_event.sound}")

entity.event_bus.register_handler(SOUND_HEARD_EVENT_TYPE, on_sound_heard)
```

## Spatial Events

The spatial extension provides several specialized events:

- `ENTITY_SEEN_EVENT_TYPE`: Triggered when an entity with Vision sees another entity with Visible
- `POSITION_UPDATED_EVENT_TYPE`: Triggered when an entity's position changes
- `SOUND_HEARD_EVENT_TYPE`: Triggered when an entity with Hearing receives a sound
- `SOUND_CREATED_EVENT_TYPE`: Triggered when an entity with Audible creates a sound

```python
from relentity.spatial.events import ENTITY_SEEN_EVENT_TYPE, SOUND_HEARD_EVENT_TYPE

# Register handlers for spatial events
entity.event_bus.register_handler(ENTITY_SEEN_EVENT_TYPE, on_entity_seen)
entity.event_bus.register_handler(SOUND_HEARD_EVENT_TYPE, on_sound_heard)
```

## Complete Simulation Example

```python
import asyncio
from relentity.spatial.registry import SpatialRegistry
from relentity.spatial.systems import MovementSystem, VisionSystem, AudioSystem
from relentity.spatial.components import Position, Velocity, Vision, Visible, Audible, Hearing
from relentity.core.entities import Entity

# Create a spatial registry
registry = SpatialRegistry()

# Create systems
movement_system = MovementSystem(registry)
vision_system = VisionSystem(registry)
audio_system = AudioSystem(registry)

# Create entities
observer = Entity[
    Position(x=0, y=0),
    Velocity(vx=1, vy=0),
    Vision(max_range=100),
    Hearing()
](registry)

target = Entity[
    Position(x=50, y=10),
    Velocity(vx=-1, vy=0),
    Visible(),
    Audible(volume=30)
](registry)

# Register event handlers
async def on_entity_seen(event):
    print(f"Entity seen at ({event.position.x}, {event.position.y})")
    # Make a sound when seeing another entity
    audible = await event.entity.get_component(Audible)
    if audible:
        audible.queue_sound(SoundEvent(event.entity, "alert", "I see you!"))

observer.event_bus.register_handler(ENTITY_SEEN_EVENT_TYPE, on_entity_seen)

# Main simulation loop
async def simulation():
    for _ in range(60):  # Run for 60 ticks
        await movement_system.update()
        await vision_system.update()
        await audio_system.update()
        await asyncio.sleep(0.1)  # 10 fps

# Run the simulation
asyncio.run(simulation())
```

## Extension Points

### Custom Spatial Components

Create specialized spatial components for your simulation:

```python
from relentity.spatial.components import Position
from relentity.core.components import Component

class Terrain(Component):
    elevation: float = 0
    friction: float = 1.0
    is_passable: bool = True
```

### Enhanced Movement Systems

Create custom movement systems that handle complex terrain:

```python
from relentity.spatial.systems import MovementSystem

class TerrainAwareMovementSystem(MovementSystem):
    async def update(self):
        async for entity in self.registry.entities_with_components(Position, Velocity):
            position = await entity.get_component(Position)
            velocity = await entity.get_component(Velocity)
            
            # Get terrain at current position (implementation detail)
            terrain = await self.get_terrain_at(position)
            
            # Apply terrain effects to movement
            if terrain and terrain.is_passable:
                modified_vx = velocity.vx * terrain.friction
                modified_vy = velocity.vy * terrain.friction
                
                position.x += modified_vx
                position.y += modified_vy
                await entity.event_bus.emit(POSITION_UPDATED_EVENT_TYPE, position)
```

This extension provides the foundation for building spatially aware simulations with the efficiency and flexibility of the core ECS framework.
