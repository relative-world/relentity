from relentity.core import Entity
from .events import TASK_PROGRESS_EVENT_TYPE, TASK_COMPLETE_EVENT_TYPE, TASK_ABANDONED_EVENT_TYPE
from .components import Task


class TaskedEntity(Entity):
    """
    Entity that can be assigned tasks and handle task-related events.

    Methods:
        set_task: Assigns a task to the entity.
        on_task_progress: Handles task progress events.
        on_task_complete: Handles task completion events.
        on_task_abandoned: Handles task abandonment events.
    """

    def __init__(self, registry, *args, **kwargs):
        super().__init__(registry, *args, **kwargs)
        self.event_bus.register_handler(TASK_PROGRESS_EVENT_TYPE, self.on_task_progress)
        self.event_bus.register_handler(TASK_COMPLETE_EVENT_TYPE, self.on_task_complete)
        self.event_bus.register_handler(TASK_ABANDONED_EVENT_TYPE, self.on_task_abandoned)

    async def set_task(self, task: Task):
        """
        Assigns a task to the entity.

        Args:
            task (Task): The task to assign.
        """
        existing_task = await self.get_component(Task, include_subclasses=True)
        if existing_task:
            await self.remove_component(type(existing_task))
            if existing_task.remaining_cycles > 0:
                await self.event_bus.emit(TASK_ABANDONED_EVENT_TYPE, existing_task)
        await self.add_component(task)

    async def on_task_progress(self, task: Task):
        """
        Handles task progress events.

        Args:
            task (Task): The task that is in progress.
        """
        pass

    async def on_task_complete(self, task: Task):
        """
        Handles task completion events.

        Args:
            task (Task): The task that has been completed.
        """
        pass

    async def on_task_abandoned(self, task: Task):
        """
        Handles task abandonment events.

        Args:
            task (Task): The task that has been abandoned.
        """
        pass
