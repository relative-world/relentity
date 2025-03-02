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

Define components for position and movement:

```python
from relentity.spatial.components import Position, Velocity

class Position(Component):
    x: float
    y: float

class Velocity(Component):
    vx: float
    vy: float
```

Entities with both components can be moved by the `MovementSystem`.

### Perception Components

Define components for vision and audio:

```python
from relentity.spatial.components import Vision, Visible, Audible, Hearing

# Vision allows entities to see others
Vision(max_range=20)
Visible(description="Description seen by others")

# Audio allows communication
Audible(volume=50)
Hearing(volume=50)
```

## AI Integration

Integrate AI using specialized components:

```python
from relentity.ai.components import AIDriven, ToolEnabledComponent
from relentity.ai.pydantic_ollama.tools import tool

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

Define the `Actor` and `Ball` entities:

```python
from relentity.core.entities import Entity
from relentity.core.components import Identity
from relentity.spatial.components import Position, Velocity, Vision, Visible, Audible, Hearing
from relentity.ai.components import AIDriven, TextPromptComponent
from relentity.ai.events import AI_RESPONSE_EVENT_TYPE
from relentity.spatial import ENTITY_SEEN_EVENT_TYPE, SOUND_HEARD_EVENT_TYPE, SOUND_CREATED_EVENT_TYPE, POSITION_UPDATED_EVENT_TYPE
from relentity.spatial.events import SoundEvent
from relentity.ai.utils import pretty_name_entity, pretty_print_event

class Actor(Entity):
    def __init__(self, registry, name, description, *args, private_info=None, model="qwen2.5:14b", **kwargs):
        super().__init__(registry, *args, **kwargs)
        self.add_component_sync(Identity(name=name, description=description))
        self.add_component_sync(Position(x=random.randint(-10, 10), y=random.randint(-10, 10)))
        self.add_component_sync(Velocity(vx=0, vy=0))

        if private_info:
            self.add_component_sync(TextPromptComponent(text=private_info))

        self.add_component_sync(AIMovementController())
        self.add_component_sync(Vision(max_range=20))
        self.add_component_sync(Visible(description=f"{name} - {description}"))
        self.add_component_sync(Audible(volume=50))
        self.add_component_sync(Hearing(volume=50))
        self.add_component_sync(AIDriven(model=model, update_interval=1))

        self.event_bus.register_handler(AI_RESPONSE_EVENT_TYPE, self.on_ai_response)
        self.event_bus.register_handler(ENTITY_SEEN_EVENT_TYPE, self.on_entity_seen)
        self.event_bus.register_handler(SOUND_HEARD_EVENT_TYPE, self.on_sound_heard_event)
        self.event_bus.register_handler(SOUND_CREATED_EVENT_TYPE, self.on_sound_created_event)
        self.event_bus.register_handler(POSITION_UPDATED_EVENT_TYPE, self.on_position_updated)

    async def on_position_updated(self, event):
        name = await pretty_name_entity(self)
        print(f"{name} position updated - {event.x}, {event.y}")

    async def on_entity_seen(self, event):
        if event.entity is self:
            return
        ai_driven = await self.get_component(AIDriven)
        await ai_driven.add_event_for_consideration(ENTITY_SEEN_EVENT_TYPE, event, hash_key=id(event.entity))

    async def on_ai_response(self, response):
        audio = await self.get_component(Audible)
        sound_event = SoundEvent(self, "speech", response.text)
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
        await ai_driven.add_event_for_consideration(SOUND_CREATED_EVENT_TYPE, sound_event)

class Ball(Entity):
    def __init__(self, registry, *args, **kwargs):
        super().__init__(registry, *args, **kwargs)
        self.add_component_sync(Identity(name="a ball", description="A ball"))
        self.add_component_sync(Position(x=0, y=1))
        self.add_component_sync(Visible(description="A large red kickball, it's well inflated and says 'Spalding' on the side."))
        self.add_component_sync(Hearing())
        self.event_bus.register_handler(SOUND_HEARD_EVENT_TYPE, self.on_sound_heard_event)

    async def on_sound_heard_event(self, sound_event):
        if "the sun" in sound_event.sound.lower():
            Entity[
                Identity(name="a mysterious door", description="A mysterious door"),
                Position(x=10, y=0),
                Visible(description="A mysterious door")
            ](self.registry)
```

### 2. Set Up the World

Define the world in a JSON file with entities and their initial properties:

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

Set up and run the simulation systems:

```python
import asyncio
from relentity.spatial.registry import SpatialRegistry
from relentity.spatial.systems import MovementSystem, VisionSystem, AudioSystem
from relentity.ai.systems import AIDrivenSystem

async def create_entity(entity_data, registry):
    entity_type = entity_data["type"]
    components = entity_data["components"]

    if entity_type == "Actor":
        entity = Actor(registry, entity_data["name"], entity_data["description"])
    elif entity_type == "Ball":
        entity = Ball(registry)
    else:
        entity = Entity(registry)

    for component_name, component_data in components.items():
        component_class = globals()[component_name]
        entity.add_component_sync(component_class(**component_data))

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

    movement_system = MovementSystem(registry)
    ai_system = AIDrivenSystem(registry)
    vision_system = VisionSystem(registry)
    audio_system = AudioSystem(registry)

    for _ in range(100):
        await movement_system.update()
        await vision_system.update()
        await ai_system.update()
        await audio_system.update()

if __name__ == "__main__":
    asyncio.run(main())
```

## How It Works

1. **Perception**: Vision and hearing components capture events from the environment.
2. **AI Processing**: The `AIDriven` component sends context to the LLM and receives decisions.
3. **Tools**: The AI can invoke tools like `set_velocity` to interact with the world.
4. **Communication**: AI responses become speech through the `Audible` component.
5. **World Rules**: Special behaviors can be triggered by events (like the "sun" keyword revealing a door).
