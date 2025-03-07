from examples.ai.inventories.tasks import MovementTask
from relentity.core import System
from relentity.spatial import Position, Velocity


class MovementTaskSystem(System):
    async def update(self, delta_time: float = 0) -> None:
        async for entity_ref in self.registry.entities_with_components(MovementTask, Position, Velocity):
            entity = await entity_ref.resolve()
            task = await entity.get_component(MovementTask)
            position = await entity.get_component(Position)
            velocity = await entity.get_component(Velocity)

            if not task:
                continue

            # Calculate direction to target
            dx = task.target_x - position.x
            dy = task.target_y - position.y
            distance = (dx**2 + dy**2) ** 0.5

            # Check if we've reached the target
            if distance <= task.proximity_threshold:
                # Stop movement
                velocity.vx = 0
                velocity.vy = 0
                # Complete the task
                task.remaining_cycles = 0
            else:
                # Update velocity toward target
                if distance > 0:
                    velocity.vx = task.speed * dx / distance
                    velocity.vy = task.speed * dy / distance
