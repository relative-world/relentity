from relentity.core import Component
from relentity.tasks.events import TASK_PROGRESS_EVENT_TYPE, TASK_COMPLETE_EVENT_TYPE, TASK_ABANDONED_EVENT_TYPE


class Task(Component):
    """
    Base component for tasks that entities can perform.

    Attributes:
        task (str): The name of the task.
        remaining_cycles (int): The number of cycles remaining to complete the task.
    """
    task: str
    remaining_cycles: int = 5

    async def task_progress_event(self):
        """
        Creates an event indicating the task's progress.

        Returns:
            tuple: A tuple containing the event type and the task instance.
        """
        return TASK_PROGRESS_EVENT_TYPE, self

    async def task_complete_event(self):
        """
        Creates an event indicating the task's completion.

        Returns:
            tuple: A tuple containing the event type and the task instance.
        """
        return TASK_COMPLETE_EVENT_TYPE, self

    async def task_abandoned(self):
        """
        Creates an event indicating the task's abandonment.

        Returns:
            tuple: A tuple containing the event type and the task instance.
        """
        return TASK_ABANDONED_EVENT_TYPE, self
