import pytest
from unittest.mock import AsyncMock, MagicMock
from relentity.tasks.systems import TaskSystem
from relentity.tasks.components import Task
from relentity.core import Registry, Entity

@pytest.fixture
def registry():
    return Registry()

@pytest.fixture
def task_system(registry):
    return TaskSystem(registry)

@pytest.fixture
def entity_with_task():
    entity = MagicMock(spec=Entity)
    task = Task(task="performing test", name="Test Task", remaining_cycles=5, required_field="value")  # Add all required fields here
    entity.get_component = AsyncMock(return_value=task)
    entity.event_bus = MagicMock()
    entity.event_bus.emit = AsyncMock()
    entity.components = {}  # Add the components attribute
    return entity, task

@pytest.mark.asyncio
async def test_task_progress_event(task_system, registry, entity_with_task):
    entity, task = entity_with_task
    registry.entities_with_components = AsyncMock(return_value=[entity])

    await task_system.update()

    entity.event_bus.emit.assert_called_with(*await task.task_progress_event())
    assert task.remaining_cycles == 4

@pytest.mark.asyncio
async def test_task_complete_event(task_system, registry, entity_with_task):
    entity, task = entity_with_task
    task.remaining_cycles = 1
    registry.entities_with_components = AsyncMock(return_value=[entity])
    registry.remove_component_from_entity = AsyncMock()  # Mock the method

    await task_system.update()

    entity.event_bus.emit.assert_called_with(*await task.task_complete_event())
    registry.remove_component_from_entity.assert_called_with(entity, type(task))
