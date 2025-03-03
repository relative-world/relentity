# relentity.core

## Overview

`relentity.core` is a modern, asynchronous Entity-Component-System (ECS) framework designed to build intelligent simulations in Python. This architecture provides a foundation for integrating AI agents as first-class cognitive entities within your simulations.

## Key Features

- **Fully Asynchronous**: Built on Python's asyncio for high-performance, non-blocking operations
- **Component-Based Design**: Modular data structures for maximum flexibility and composition
- **Event-Driven Architecture**: Decoupled communication via a powerful event system
- **AI-Ready Integration**: Seamless integration points for AI agents and behaviors
- **Type-Safe Interfaces**: Leveraging Pydantic for reliable data validation and serialization

## Core Architecture

### Components: Pure Data

Components are stateful data containers implemented as Pydantic models, providing automatic validation and serialization:

```python
from relentity.core.components import Component

class Health(Component):
    current: int
    maximum: int = 100
    
class Inventory(Component):
    capacity: int = 10
    items: list = []
```

### Entities: Composable Objects

Entities are dynamic containers for components with a flexible composition system:

```python
# Create entity templates with composition syntax
Player = Entity[
    Position(x=0, y=0),
    Velocity(),
    Health(current=100, maximum=100)
]

# Instantiate entities from templates
player = Player(registry)

# Access components asynchronously
health = await player.get_component(Health)
health.current -= 10
```

### Registry: Efficient Queries

The Registry tracks entities and enables high-performance component queries:

```python
# Find all entities with specific components
async for entity in registry.entities_with_components(Position, Health):
    position = await entity.get_component(Position)
    health = await entity.get_component(Health)
    
    # Process entities with these components
    if health.current < health.maximum * 0.2:
        # Entity is at low health
        await apply_healing(entity, position)
```

### Systems: Logic Processors

Systems contain logic that processes entities with specific component combinations:

```python
class MovementSystem(System):
    async def update(self):
        async for entity in self.registry.entities_with_components(Position, Velocity):
            position = await entity.get_component(Position)
            velocity = await entity.get_component(Velocity)
            
            # Apply movement logic
            position.x += velocity.vx
            position.y += velocity.vy
```

### EventBus: Decoupled Communication

The EventBus provides a sophisticated publish-subscribe mechanism:

```python
# Register event handlers
entity.event_bus.register_handler("collision.*", on_collision)
entity.event_bus.register_handler("damage.physical", on_physical_damage)

# Emit events
await entity.event_bus.emit("collision.wall", collision_data)
```

## AI Integration

The framework is designed with AI integration as a core principle, enabling:

1. **AI-Driven Components**: Represent AI state, beliefs, and knowledge
2. **AI System Integration**: Systems that process entities through AI models
3. **Cognitive Event Patterns**: Communication between AI agents and environment
4. **Tool-Based Interaction**: Structured function calling for LLMs

Example AI integration:

```python
class CognitiveSystem(System):
    async def update(self):
        async for entity in self.registry.entities_with_components(Cognitive, Perception):
            cognitive = await entity.get_component(Cognitive)
            perception = await entity.get_component(Perception)
            
            # Process entity perceptions through AI model
            response = await cognitive.model.process(perception.observations)
            
            # Update entity's internal state based on AI processing
            await entity.add_component(Decision(action=response.action))
```

## Complete Workflow Example

```python
# Setup registry and systems
registry = Registry()
movement_system = MovementSystem(registry)
physics_system = PhysicsSystem(registry)
ai_system = AgentSystem(registry)

# Create entities
player = Player(registry)
agent = AIAgent(registry)

# Main simulation loop
async def simulation_loop():
    while True:
        # Process systems in order
        await physics_system.update()
        await ai_system.update()
        await movement_system.update()
        
        # Yield control to event loop
        await asyncio.sleep(1/60)  # 60 FPS
```
