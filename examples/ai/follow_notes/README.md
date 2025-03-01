# Building AI-Driven Virtual Environments with Entity Component Systems

## Introduction

This tutorial explores how to create intelligent virtual agents using an Entity Component System (ECS) architecture with Large Language Models (LLMs). We'll use the `relentity` framework to build agents that can perceive, communicate, and navigate a virtual environment.

## Understanding Entity Component Systems

At its core, ECS architecture separates:

- **Entities**: Containers that represent objects in the world
- **Components**: Data containers attached to entities
- **Systems**: Logic that processes entities with specific components

This separation allows for flexible, modular design where behavior emerges from component combinations.

## Core Components

### Position and Movement

```python
class Position(Component):
    x: float
    y: float

class Velocity(Component):
    vx: float
    vy: float
```

Entities with both components can be moved by the `MovementSystem`.

### Perception Components

```python
# Vision allows entities to see others
Vision(max_range=20)
Visible(description="Description seen by others")

# Audio allows communication
Audible(volume=50)
Hearing(volume=50)
```

## AI Integration

The LLM integration happens through several specialized components:

```python
# Core AI component that manages model interactions
AIDriven(model="qwen2.5:14b", update_interval=1)

# Enables tools the AI can use
class AIMovementController(ToolEnabledComponent):
    @tool
    async def set_velocity(self, actor, vx: float, vy: float):
        velocity = await actor.get_component(Velocity)
        if velocity:
            velocity.vx = float(vx)
            velocity.vy = float(vy)
```

## Event System

Entities communicate through an event system:

1. `ENTITY_SEEN_EVENT_TYPE`: Triggered when an entity sees another
2. `SOUND_HEARD_EVENT_TYPE`: Triggered when an entity hears a sound
3. `AI_RESPONSE_EVENT_TYPE`: Triggered when an AI generates a response

## Creating the Simulation

### 1. Define Entities

```python
class Actor(Entity):
    def __init__(self, registry, name, description, *args, **kwargs):
        super().__init__(registry, *args, **kwargs)
        # Add components
        self.add_component_sync(Identity(name=name, description=description))
        self.add_component_sync(Position(x=random.randint(-10, 10), y=random.randint(-10, 10)))
        # ... add other components
```

### 2. Set Up the World

The world is defined in a JSON file with entities and their initial properties:

```json
{
  "entities": [
    {
      "type": "Actor",
      "name": "Dave",
      "description": "A person that woke up in an endless field of grass...",
      "components": {
        // Component configurations
      }
    },
    // Other entities
  ]
}
```

### 3. Run the Simulation Systems

```python
async def main():
    registry = SpatialRegistry()
    # Load entities
    
    # Set up systems
    movement_system = MovementSystem(registry)
    ai_system = AIDrivenSystem(registry)
    vision_system = VisionSystem(registry)
    audio_system = AudioSystem(registry)
    
    # Run simulation loop
    for _ in range(100):
        await movement_system.update()
        await vision_system.update()
        await ai_system.update()
        await audio_system.update()
```

## How It Works

1. **Perception**: Vision and hearing components capture events from the environment
2. **AI Processing**: The `AIDriven` component sends context to the LLM and receives decisions
3. **Tools**: The AI can invoke tools like `set_velocity` to interact with the world
4. **Communication**: AI responses become speech through the `Audible` component
5. **World Rules**: Special behaviors can be triggered by events (like the "sun" keyword revealing a door)
