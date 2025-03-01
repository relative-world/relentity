from relentity.core import Registry
from relentity.spatial.systems import MovementSystem
from relentity.tasks.components import Task
from relentity.tasks.entities import TaskedEntity
from relentity.tasks.systems import TaskSystem


class BookReading(Task):
    task: str = "reading a book"
    book_title: str
    remaining_cycles: int = 5


class PettingDog(Task):
    task: str = "petting the dog"
    remaining_cycles: int = 3


async def start_reading(self, book_title="The Great Gatsby", duration=4):
    await self.set_task(BookReading(book_title="This is a book"))


async def pet_dog(self):
    await self.set_task(PettingDog())


class EngagedActor(TaskedEntity):

    async def start_reading(self, book_title="The Great Gatsby", duration=4):
        await self.set_task(BookReading(book_title="This is a book"))

    async def start_petting_dog(self):
        await self.set_task(PettingDog())

    async def on_task_complete(self, task: Task):
        print(f"Task complete: {task}")

    async def on_task_progress(self, task: Task):
        print(f"Task progress: {task}")

    async def on_task_abandoned(self, task):
        print(f"Task abandoned: {task}")


async def main():
    registry = Registry()

    reader = EngagedActor[Task(task="petting dog"),](registry, "Alice")
    # await reader.start_reading()

    task_system = TaskSystem(registry=registry)
    movement_system = MovementSystem(registry=registry)

    while True:
        await task_system.update()
        await movement_system.update()
        await asyncio.sleep(0.5)  # To see the progression


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
