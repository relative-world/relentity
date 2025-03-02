from unittest.mock import AsyncMock

import pytest

from relentity.core import Registry
from relentity.tasks import TaskSystem
from relentity.tasks.components import Task
from relentity.tasks.entities import TaskedEntity


class MockTask(Task):
    task: str = "mock task"
    remaining_cycles: int = 1


@pytest.fixture
async def registry():
    return Registry()


@pytest.fixture
async def tasked_entity(registry):
    class MockTaskEntity(TaskedEntity):
        on_task_progress = AsyncMock()
        on_task_complete = AsyncMock()
        on_task_abandoned = AsyncMock()

    return MockTaskEntity(registry)


@pytest.mark.asyncio
async def test_set_task(tasked_entity):
    task = MockTask()
    await tasked_entity.set_task(task)
    assert await tasked_entity.get_component(MockTask) is not None


@pytest.mark.asyncio
async def test_on_task_progress(registry, tasked_entity):
    task = MockTask()
    await tasked_entity.set_task(task)
    task_system = TaskSystem(registry)
    await task_system.update()
    tasked_entity.on_task_progress.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_task_complete(registry, tasked_entity):
    task = MockTask()
    await tasked_entity.set_task(task)
    task_system = TaskSystem(registry)
    await task_system.update()
    tasked_entity.on_task_complete.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_task_abandoned(registry, tasked_entity):
    task = MockTask()
    await tasked_entity.set_task(task)
    await tasked_entity.set_task(MockTask())
    tasked_entity.on_task_abandoned.assert_awaited_once()
