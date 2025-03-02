from relentity.core import System
from relentity.tasks.components import Task


class TaskSystem(System):
    """
    System for managing tasks assigned to entities.

    Methods:
        update: Processes tasks for entities, updating their progress and handling completion.
    """

    async def update(self):
        """
        Updates the system by processing all entities with Task components.
        Decrements the remaining cycles for each task and emits progress events.
        If a task is completed, emits a completion event and removes the task component from the entity.
        """
        async for entity in self.registry.entities_with_components(Task, include_subclasses=True):
            task = await entity.get_component(Task, include_subclasses=True)

            if task:
                task.remaining_cycles -= 1
                await entity.event_bus.emit(*(await task.task_progress_event()))

                if task.remaining_cycles <= 0:
                    await entity.event_bus.emit(*(await task.task_complete_event()))
                    await self.registry.remove_component_from_entity(entity, type(task))
