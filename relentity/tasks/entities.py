from relentity.core import Entity
from relentity.spatial.components import Position
from relentity.tasks.components import Task
from relentity.tasks.events import TASK_PROGRESS_EVENT_TYPE, TASK_COMPLETE_EVENT_TYPE, TASK_ABANDONED_EVENT_TYPE


class TaskedEntity(Entity):
    def __init__(self, registry, name, *args, **kwargs):
        super().__init__(registry, *args, **kwargs)
        self.add_component_sync(Position(x=0, y=0))
        self.event_bus.register_handler(TASK_PROGRESS_EVENT_TYPE, self.on_task_progress)
        self.event_bus.register_handler(TASK_COMPLETE_EVENT_TYPE, self.on_task_complete)
        self.event_bus.register_handler(TASK_ABANDONED_EVENT_TYPE, self.on_task_abandoned)

    async def set_task(self, task: Task):
        existing_task = await self.get_component(Task, include_subclasses=True)
        if existing_task:
            await self.remove_component(type(existing_task))
            await self.event_bus.emit(TASK_ABANDONED_EVENT_TYPE, existing_task)
        await self.add_component(task)

    async def on_task_progress(self, task):
        pass

    async def on_task_complete(self, task):
        await self.remove_component(type(task))

    async def on_task_abandoned(self, task):
        await self.remove_component(type(task))
