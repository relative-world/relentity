import random

from relentity.core import Registry
from relentity.tasks import Task, TaskedEntity, TaskSystem


class BookReading(Task):
    task: str = "reading a book"
    book_title: str
    remaining_cycles: int = 5


class PettingDog(Task):
    task: str = "petting the dog"
    remaining_cycles: int = 3


class EngagedActor(TaskedEntity):
    async def start_reading(self, book_title="The Great Gatsby", duration=4):
        await self.set_task(BookReading(book_title=book_title, remaining_cycles=duration))

    async def start_petting_dog(self):
        await self.set_task(PettingDog())

    async def start_new_random_task(self):
        await random.choice([self.start_reading, self.start_petting_dog])()

    async def on_task_complete(self, task: Task):
        await self.start_new_random_task()
        print(f"Task complete: {task}")

    async def on_task_progress(self, task: Task):
        print(f"Task progress: {task}")

    async def on_task_abandoned(self, task):
        print(f"Task abandoned: {task}")


async def main():
    registry = Registry()
    task_system = TaskSystem(registry=registry)

    # side effects rule
    EngagedActor[Task(task="petting dog")](registry)

    while True:
        await task_system.update()
        await asyncio.sleep(0.5)  # To see the progression


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
