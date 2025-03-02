# relentity.core

## Overview

`relentity.core` is an asynchronous Entity-Component-System (ECS) framework for building simulations in Python. The framework provides a modular and flexible architecture where:

- **Entities** represent objects in your simulation
- **Components** store data about these objects
- **Systems** process entities with specific component sets
- **Events** allow communication between different parts of the system

## Architecture

The core system follows these principles:

1. Entities are containers for components
2. Components are pure data structures
3. Systems contain logic and operate on entities with specific component types
4. The Registry maintains relationships between entities and components
5. The EventBus enables decoupled communication

## Core Classes

### Component

Components are Pydantic models that store entity data with validation.

```python
from relentity.core.components import Component

class Health(Component):
    current: int
    maximum: int = 100
```

Components can be extended to create specialized data containers for any simulation needs.

### Entity

Entities are containers for components that provide an interface for querying and modifying components.

```python
# Creating entities with components
Player = Entity[
    Position(x=0, y=0),
    Velocity(vx=0, vy=0),
    Health(current=100, maximum=100)
]

player = Player(registry)
```

Key capabilities:
- Component management (add/remove/get)
- Event bus integration
- Registry association

### Registry

The Registry tracks all entities and provides efficient queries for entities with specific components.

```python
# Find all entities with both Position and Velocity components
async for entity in registry.entities_with_components(Position, Velocity):
    position = await entity.get_component(Position)
    # Process entity...
```

The Registry provides the foundation for systems to efficiently process only relevant entities.

### System

Systems contain the logic that operates on entities with specific component sets.

```python
class MovementSystem(System):
    async def update(self):
        async for entity in self.registry.entities_with_components(Position, Velocity):
            position = await entity.get_component(Position)
            velocity = await entity.get_component(Velocity)
            position.x += velocity.vx
            position.y += velocity.vy
```

Systems can be extended to implement any simulation logic required.

### EventBus

The EventBus provides a publish-subscribe mechanism for communication between components.

```python
# Register an event handler
entity.event_bus.register_handler("collision", on_collision)

# Emit an event
await entity.event_bus.emit("collision", collision_data)
```

The EventBus supports wildcard patterns for flexible event handling.

### EntityMeta

The EntityMeta metaclass provides syntactic sugar for entity composition using square bracket notation.

```python
# Create specialized entity types using component composition
Monster = Entity[
    Position(x=10, y=10),
    Health(current=50, maximum=50)
]
```

## Extension Points

### Creating Custom Components

Define new component types by subclassing `Component` with Pydantic fields:

```python
class Inventory(Component):
    items: List[Item] = []
    capacity: int = 10
```

### Implementing Custom Systems

Create specialized simulation logic by subclassing `System` and implementing `update()`:

```python
class CombatSystem(System):
    async def update(self):
        async for entity in self.registry.entities_with_components(Health, Weapon):
            # Combat logic here
```

### Event-Driven Communication

Implement decoupled interactions using events:

```python
async def on_damage(damage_data):
    # Handle damage event
    pass

entity.event_bus.register_handler("damage.physical", on_damage)
```

## Complete Workflow Example

```python
# Create registry and entities
registry = Registry()
player = Entity[Position(x=0, y=0), Velocity(vx=0, vy=0)](registry)

# Create systems
movement_system = MovementSystem(registry)

# Main simulation loop
async def main():
    while True:
        # Update all systems
        await movement_system.update()
        # Process other game logic
        await asyncio.sleep(1/60)  # 60 FPS
```

This framework provides the foundation for building complex, modular simulations with clean separation of data and logic.
