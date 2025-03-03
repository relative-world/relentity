# Relentity

![multivariant-tests](https://github.com/relative-world/relentity/blob/main/.github/workflows/multivariant-tests.yml/badge.svg)

## Overview

Relentity is an asynchronous Entity-Component-System (ECS) framework for building simulations, games, and AI environments in Python. It provides a modular architecture designed for flexibility and extensibility.

## Features

- **Core ECS Architecture**: Entities, components, systems, and events
- **Spatial Extensions**: Position tracking, vision, hearing, and spatial queries
- **Task Management**: Task assignment, progress tracking, and completion events
- **AI Integration**: AI-driven entities, tool-based interactions, and event-aware agents
- **Asynchronous Design**: Built for efficient concurrent processing

## Core Modules

### [relentity.core](relentity/core/README.md)

The foundation of the framework providing the base ECS architecture:

```python
from relentity.core import Registry, Entity, Component, System

# Define components
class Health(Component):
    current: int
    maximum: int = 100

# Create entities
player = Entity[Health(current=100)](registry)

# Create and run systems
class HealthSystem(System):
    async def update(self):
        async for entity in self.registry.entities_with_components(Health):
            health = await entity.get_component(Health)
            # Process health logic...
```

### [relentity.spatial](relentity/spatial/README.md)

Extensions for spatial simulations including position, movement, vision and sound:

```python
from relentity.spatial import SpatialRegistry
from relentity.spatial.components import Position, Velocity, Vision, Visible

registry = SpatialRegistry()
observer = Entity[
    Position(x=0, y=0),
    Velocity(vx=1, vy=0),
    Vision(max_range=100)
](registry)
```

### [relentity.ai](relentity/ai/README.md)

AI-driven entity behavior using LLM models:

```python
from relentity.ai.components import AIDriven, ToolEnabledComponent
from relentity.ai.systems import AIDrivenSystem

# Create AI-driven entity
agent = Entity[
    Position(x=0, y=0),
    AIDriven(model="llama3", update_interval=1)
](registry)

# Process AI decisions
ai_system = AIDrivenSystem(registry)
await ai_system.update()
```

### [relentity.tasks](relentity/tasks/README.md)

Task management for entity behavior:

```python
from relentity.tasks.entities import TaskedEntity
from relentity.tasks.components import Task

# Create custom tasks
class BuildTask(Task):
    task: str = "build"
    structure: str = "house"
    remaining_cycles: int = 10

# Assign task to entity
builder = TaskedEntity(registry, "Builder")
await builder.set_task(BuildTask())
```

## Configuration

Relentity uses environment variables and a configuration file to manage settings. The primary configuration is handled through the `RelentitySettings` class in `relentity/settings.py`, which uses `pydantic_settings` for validation and management.

### Environment Variables

Configuration can be provided via environment variable or a `.env` file. Here are the key variables:

- `relentity_base_url`: The base URL for the Ollama service (for AI components).
- `relentity_default_model`: The default model used by the AI components.
- `relentity_json_fix_model`: The model used for JSON fixes.
- `relentity_model_keep_alive`: The duration (in seconds) to keep the model alive.

Example `.env` file:
```dotenv
relentity_base_url=http://192.168.1.14:11434
relentity_default_model="qwen2.5:14b"
relentity_json_fix_model="qwen2.5:14b"
relentity_model_keep_alive=300.0
```

## Complete Example

```python
import asyncio
from relentity.spatial import SpatialRegistry
from relentity.core import Entity, Identity
from relentity.spatial.components import Position, Velocity, Vision, Visible
from relentity.spatial.systems import MovementSystem, VisionSystem
from relentity.spatial.events import ENTITY_SEEN_EVENT_TYPE

# Create registry and systems
registry = SpatialRegistry()
movement_system = MovementSystem(registry)
vision_system = VisionSystem(registry)

# Create entities
observer = Entity[
    Identity(name="Observer"),
    Position(x=0, y=0),
    Velocity(vx=1, vy=0),
    Vision(max_range=100)
](registry)

target = Entity[
    Identity(name="Target"),
    Position(x=50, y=10),
    Visible()
](registry)

# Register event handlers
async def on_entity_seen(event):
    print(f"Entity seen at ({event.position.x}, {event.position.y})")

observer.event_bus.register_handler(ENTITY_SEEN_EVENT_TYPE, on_entity_seen)

# Main simulation loop
async def simulation():
    for _ in range(60):  # Run for 60 ticks
        await movement_system.update()
        await vision_system.update()
        await asyncio.sleep(0.1)  # 10 fps

# Run the simulation
asyncio.run(simulation())
```

## Module Documentation

For detailed documentation on each module:

- [relentity.core](relentity/core/README.md) - Core ECS framework
- [relentity.spatial](relentity/spatial/README.md) - Spatial simulation extensions
- [relentity.ai](relentity/ai/README.md) - AI-driven entities
- [relentity.tasks](relentity/tasks/README.md) - Task management system

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
