from examples.ai.inventories.tasks import MovementTask
from relentity.ai import ToolEnabledComponent, tool, SystemPromptRenderableComponent
from relentity.spatial import Velocity


class AIMovementController(ToolEnabledComponent):
    @tool
    async def stop_movement(self, actor):
        velocity = await actor.get_component(Velocity)
        if velocity:
            velocity.vx = 0
            velocity.vy = 0

    @tool
    async def go_to_coordinates(self, actor, x: float, y: float) -> str:
        """Move to the specified coordinates"""
        # Create and assign a movement task
        movement_task = MovementTask(target_x=x, target_y=y)
        await actor.set_task(movement_task)
        return f"Moving to coordinates ({x}, {y})"


class GoalTrackingController(SystemPromptRenderableComponent, ToolEnabledComponent):
    goal_stack: list[str] = []

    async def render_system_prompt(self) -> str:
        print(f">>> Current goals (priority order): {', '.join(self.goal_stack[:5])}")
        return f"Current short term goals (priority order): {', '.join(self.goal_stack[:5])}"

    @tool
    async def add_task_to_tracker(self, actor, goal: str) -> str:
        """Add a task you wish to track.  Surfaced on every evaluation cycle.  If one is not currently set, set one."""
        await actor.emit("goal.added", goal=goal)
        self.goal_stack.append(goal)

    @tool
    async def mark_current_task_done(self, actor):
        goal = self.goal_stack[-1]
        await actor.emit("goal.complete", goal=goal)
        self.goal_stack = self.goal_stack[:-1]
