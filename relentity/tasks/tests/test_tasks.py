import pytest
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
def entity_with_task(registry):
    entity = Entity(registry)
    task = Task(task="performing test", name="Test Task", remaining_cycles=5, required_field="value")
    entity.components = {Task: task}
    return entity, task


@pytest.mark.asyncio
async def test_task_progress_event(task_system, registry, entity_with_task):
    entity, task = entity_with_task
    registry.register_entity(entity)

    await task_system.update()

    assert task.remaining_cycles == 4


@pytest.mark.asyncio
async def test_task_complete_event(task_system, registry, entity_with_task):
    entity, task = entity_with_task
    task.remaining_cycles = 1
    registry.register_entity(entity)

    await task_system.update()

    assert task.remaining_cycles == 0
    assert entity not in registry.entities
