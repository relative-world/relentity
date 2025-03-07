from relentity.tasks import Task


class MovementTask(Task):
    task: str = "moving to coordinates"
    target_x: float
    target_y: float
    speed: float = 50.0
    proximity_threshold: float = 5.0
    remaining_cycles: int = 100  # Will be completed when reaching target
