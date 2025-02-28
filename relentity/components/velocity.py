from math import sqrt

from relentity.components import Component
from relentity.components.ai_agents import AiAgentPromptRenderable, AIAgent
from relentity.components.tools import TooledMixin
from relentity.pydantic_ollama.tools import tool


class Velocity(AiAgentPromptRenderable, Component):
    vx: float
    vy: float

    async def render(self, agent: AIAgent):
        """Render the velocity component for an AI agent."""
        self.apply_velocity_bounds()
        magnitude = sqrt(self.vx**2 + self.vy**2)
        max_speed = 10
        scaled_actitivies = ['shuffling', 'walking', 'hustling', 'running', 'sprinting']
        activity = scaled_actitivies[min(int(magnitude / max_speed * len(scaled_actitivies)), len(scaled_actitivies)-1)]
        return f"Movement: You are currently {activity} in the direction {self.vx}, {self.vy}"

    def apply_velocity_bounds(self):
        magnitude = sqrt(self.vx**2 + self.vy**2)
        max_speed = 10
        if magnitude > max_speed:
            scale = max_speed / magnitude
            self.vx *= scale
            self.vy *= scale



class TooledVelocity(TooledMixin, Component):

    @tool
    async def set_desired_velocity(self, actor, vx: float, vy: float):
        """Move the entity to the specified coordinates."""
        vx = float(vx)
        vy = float(vy)
        velocity = await actor.get_component(Velocity)
        velocity.vx = vx
        velocity.vy = vy
        velocity.apply_velocity_bounds()
