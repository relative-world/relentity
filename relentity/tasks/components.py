from relentity.core import Component
from relentity.tasks.events import TASK_PROGRESS_EVENT_TYPE, TASK_COMPLETE_EVENT_TYPE, TASK_ABANDONED_EVENT_TYPE


class Task(Component):
    task: str
    remaining_cycles: int = 5

    async def task_progress_event(self):
        return TASK_PROGRESS_EVENT_TYPE, self

    async def task_complete_event(self):
        return TASK_COMPLETE_EVENT_TYPE, self

    async def task_abandoned(self):
        return TASK_ABANDONED_EVENT_TYPE, self
