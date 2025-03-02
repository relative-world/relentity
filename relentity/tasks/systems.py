from relentity.core import System
from relentity.tasks.components import Task


class TaskSystem(System):
    async def update(self):
        entities = await self.registry.entities_with_components(Task, include_subclasses=True)
        for entity in entities:
            task = await entity.get_component(Task, include_subclasses=True)

            if task:
                task.remaining_cycles -= 1
                await entity.event_bus.emit(*(await task.task_progress_event()))

                if task.remaining_cycles <= 0:
                    await entity.event_bus.emit(*(await task.task_complete_event()))
                    await self.registry.remove_component_from_entity(entity, type(task))