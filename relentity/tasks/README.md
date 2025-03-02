# relentity.tasks

## Overview

`relentity.tasks` extends the `relentity.core` framework to provide a task management system for entities. This module enables:

- Assigning tasks to entities
- Tracking task progress over time
- Handling task completion or abandonment
- Automatic task processing through a dedicated system

This extension maintains the core ECS architecture while adding functionality for behavior management in simulations, games, and AI environments.

## Core Task Components

### Task

Base component for all tasks that entities can perform.

```python
from relentity.tasks.components import Task

# Create a custom task with 5 cycles to complete
class HarvestTask(Task):
    task: str = "harvest"
    resource_id: str = "wood"
```

## Task Entity

### TaskedEntity

A specialized entity type that can be assigned tasks and handle task-related events.

```python
from relentity.tasks.entities import TaskedEntity

# Create an entity that can handle tasks
worker = TaskedEntity(registry, "Worker")

# Assign a task to the entity
await worker.set_task(HarvestTask(resource_id="stone"))
```

## Task System

### TaskSystem

Processes all entities with Task components, progressing tasks until completion.

```python
from relentity.tasks.systems import TaskSystem

# Create and initialize the task system
task_system = TaskSystem(registry)

# Update tasks in the simulation loop
await task_system.update()
```

## Task Events

The tasks extension provides several specialized events:

- `TASK_PROGRESS_EVENT_TYPE`: Triggered when a task progresses (each cycle)
- `TASK_COMPLETE_EVENT_TYPE`: Triggered when a task reaches completion
- `TASK_ABANDONED_EVENT_TYPE`: Triggered when a task is abandoned

```python
from relentity.tasks.events import TASK_PROGRESS_EVENT_TYPE, TASK_COMPLETE_EVENT_TYPE, TASK_ABANDONED_EVENT_TYPE

# Define event handlers
async def on_task_progress(task):
    print(f"Task '{task.task}' in progress: {task.remaining_cycles} cycles left")

async def on_task_complete(task):
    print(f"Task '{task.task}' completed!")

# Register event handlers
entity.event_bus.register_handler(TASK_PROGRESS_EVENT_TYPE, on_task_progress)
entity.event_bus.register_handler(TASK_COMPLETE_EVENT_TYPE, on_task_complete)
```

## Complete Example

```python
import asyncio
from relentity.core import Registry, Entity
from relentity.spatial.components import Position
from relentity.tasks.components import Task
from relentity.tasks.entities import TaskedEntity
from relentity.tasks.systems import TaskSystem
from relentity.tasks.events import TASK_PROGRESS_EVENT_TYPE, TASK_COMPLETE_EVENT_TYPE

# Create custom tasks
class BuildTask(Task):
    task: str = "build"
    structure: str = "house"
    remaining_cycles: int = 10

class GatherTask(Task):
    task: str = "gather"
    resource: str = "wood"
    remaining_cycles: int = 5

# Initialize registry and systems
registry = Registry()
task_system = TaskSystem(registry)

# Create workers
builder = TaskedEntity(registry, "Builder")
gatherer = TaskedEntity(registry, "Gatherer")

# Define event handlers
async def on_task_progress(task):
    if task.task == "build":
        print(f"Building {task.structure}... {task.remaining_cycles} cycles left")
    elif task.task == "gather":
        print(f"Gathering {task.resource}... {task.remaining_cycles} cycles left")

async def on_task_complete(task):
    if task.task == "build":
        print(f"Finished building {task.structure}!")
    elif task.task == "gather":
        print(f"Finished gathering {task.resource}!")

# Register event handlers
builder.event_bus.register_handler(TASK_PROGRESS_EVENT_TYPE, on_task_progress)
builder.event_bus.register_handler(TASK_COMPLETE_EVENT_TYPE, on_task_complete)
gatherer.event_bus.register_handler(TASK_PROGRESS_EVENT_TYPE, on_task_progress)
gatherer.event_bus.register_handler(TASK_COMPLETE_EVENT_TYPE, on_task_complete)

# Main simulation loop
async def simulation():
    # Assign initial tasks
    await builder.set_task(BuildTask())
    await gatherer.set_task(GatherTask())
    
    # Run for 12 cycles
    for _ in range(12):
        await task_system.update()
        await asyncio.sleep(1)  # 1 second between updates
        
        # After gatherer completes first task, assign a new one
        if _ == 6:
            await gatherer.set_task(GatherTask(resource="stone"))

# Run the simulation
asyncio.run(simulation())
```

## Extension Points

### Custom Tasks

Create specialized task components by subclassing `Task`:

```python
class CombatTask(Task):
    task: str = "combat"
    target_id: str
    damage_per_cycle: int = 10
    remaining_cycles: int = 3
    
    async def task_progress_event(self):
        # Custom event data for combat progress
        return TASK_PROGRESS_EVENT_TYPE, self
```

### Enhanced Task Entities

Create entity subclasses with specialized task handling:

```python
class WorkerEntity(TaskedEntity):
    async def on_task_progress(self, task):
        # Special handling for worker tasks
        if task.task == "harvest":
            # Update worker's resources
            await self.add_resource(task.resource_id, 1)
```

This module provides the foundation for building task-based behavior in simulations with the efficiency and flexibility of the core ECS framework.