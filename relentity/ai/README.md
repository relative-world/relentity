# relentity.ai

## Overview

`relentity.ai` extends the `relentity.core` framework to provide AI-driven behavior for entities in simulations. This module enables:

- Entities controlled by AI models
- Tool-based interactions between AI and the simulation
- Event-aware AI agents that can respond to their environment
- Customizable prompts and system messages

This extension maintains the core ECS architecture while adding functionality for intelligent agent behavior in simulations, games, and AI environments.

## Core AI Components

### AIDriven

Base component that marks an entity to be controlled by an AI agent.

```python
from relentity.ai.components import AIDriven

# Create an entity driven by the default AI model
entity = Entity[
    Identity(name="AIAgent", description="An AI-controlled entity"),
    Position(x=0, y=0),
    AIDriven(model="llama3", update_interval=5)
](registry)
```

### PromptRenderableComponent & SystemPromptRenderableComponent

Interfaces for components that can contribute to the AI prompt and system prompt.

```python
from relentity.ai.components import TextPromptComponent, TextSystemPromptComponent

# Add text components to contribute to prompts
entity.add_component(TextPromptComponent(text="What should I do next?"))
entity.add_component(TextSystemPromptComponent(
    text="You are an explorer in a simulated world. Think carefully about your surroundings."
))
```

### ToolEnabledComponent

Components with this mixin can expose tools to the AI system using the `@tool` decorator.

```python
from relentity.ai.components import ToolEnabledComponent
from relentity.ai.pydantic_ollama.tools import tool

class MovementTools(ToolEnabledComponent):
    @tool
    async def move_north(self, actor) -> str:
        """Move the entity north by one unit"""
        position = await actor.get_component(Position)
        position.y += 1
        return f"Moved north to position ({position.x}, {position.y})"
```

## AI System

### AIDrivenSystem

Processes entities with the AIDriven component, generating prompts and handling AI responses.

```python
from relentity.ai.systems import AIDrivenSystem

# Create the AI system
ai_system = AIDrivenSystem(registry)

# Include in the simulation update loop
await ai_system.update()
```

## AI Events

The AI extension provides event types for communication:

- `AI_RESPONSE_EVENT_TYPE`: Triggered when the AI generates a response

```python
from relentity.ai.events import AI_RESPONSE_EVENT_TYPE

# Register a handler for AI responses
async def on_ai_response(response):
    print(f"AI decided to: {response}")

entity.event_bus.register_handler(AI_RESPONSE_EVENT_TYPE, on_ai_response)
```

## AI Utilities

### Event Formatting

Utilities to format events for AI consumption.

```python
from relentity.ai.utils import pretty_print_event

# Format an event for AI consumption
event_text = await pretty_print_event("entity_seen", entity_seen_event)
```

## Complete Example

```python
import asyncio
from relentity.core import Registry, Identity
from relentity.spatial.components import Position
from relentity.spatial import Visible, Audible, Hearing
from relentity.spatial.registry import SpatialRegistry
from relentity.spatial.systems import MovementSystem
from relentity.ai.components import AIDriven, TextSystemPromptComponent, ToolEnabledComponent
from relentity.ai.systems import AIDrivenSystem
from relentity.ai.pydantic_ollama.tools import tool


# Define custom tools
class ExplorerTools(ToolEnabledComponent):
    @tool
    async def move(self, actor, direction: str) -> str:
        """Move in the specified direction (north, south, east, west)"""
        position = await actor.get_component(Position)
        if direction == "north":
            position.y += 1
        elif direction == "south":
            position.y -= 1
        elif direction == "east":
            position.x += 1
        elif direction == "west":
            position.x -= 1
        return f"Moved {direction} to position ({position.x}, {position.y})"

    @tool
    async def say(self, actor, message: str) -> str:
        """Say something out loud"""
        audible = await actor.get_component(Audible)
        from relentity.spatial.events import SoundEvent
        audible.queue_sound(SoundEvent(actor, "voice", message))
        return f"Said: {message}"


# Initialize registry and systems
registry = SpatialRegistry()
movement_system = MovementSystem(registry)
ai_system = AIDrivenSystem(registry)

# Create AI-driven entity
agent = Entity[
    Identity(name="Explorer", description="An AI-controlled explorer"),
    Position(x=0, y=0),
    Visible(description="A curious explorer"),
    Audible(volume=50),
    Hearing(),
    AIDriven(model="llama3", update_interval=1),
    ExplorerTools(),
    TextSystemPromptComponent(
        text="You are an explorer in a simulated world. Use your tools to move around and interact.")
](registry)

# Create environment entity
landmark = Entity[
    Identity(name="Ancient Tree", description="A massive ancient tree"),
    Position(x=5, y=5),
    Visible(description="A towering tree with glowing leaves")
](registry)


# Main simulation loop
async def simulation():
    for _ in range(20):  # Run for 20 cycles
        await movement_system.update()
        await ai_system.update()
        await asyncio.sleep(1)  # 1 second between updates


# Run the simulation
asyncio.run(simulation())
```

## Extension Points

### Custom AI Components

Create specialized AI components for your simulation:

```python
from relentity.ai.components import AIDriven

class SpecializedAgent(AIDriven):
    personality: str = "friendly"
    goals: list[str] = ["explore", "gather resources"]
    
    async def render_system_prompt(self):
        base_prompt = await super().render_system_prompt()
        return f"{base_prompt}\nYou have a {self.personality} personality and your goals are: {', '.join(self.goals)}."
```

### Custom Tool Components

Implement domain-specific tools for AI interaction:

```python
class CombatTools(ToolEnabledComponent):
    @tool
    async def attack(self, actor, target_id: str) -> str:
        """Attack a target by ID"""
        # Implementation details for combat
        return f"Attacked {target_id}"
```

This module provides the foundation for building intelligent agent behavior in simulations with the efficiency and flexibility of the core ECS framework.
