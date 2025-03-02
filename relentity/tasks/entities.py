from relentity.core import Entity
from relentity.tasks.components import Task


class TaskedEntity(Entity):
    """
    Entity that can be assigned tasks and handle task-related events.

    Methods:
        set_task: Assigns a task to the entity.
        on_task_progress: Handles task progress events.
        on_task_complete: Handles task completion events.
        on_task_abandoned: Handles task abandonment events.
    """

    async def set_task(self, task: Task):
        """
        Assigns a task to the entity.

        Args:
            task (Task): The task to assign.
        """
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
