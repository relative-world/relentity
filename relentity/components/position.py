from relentity.components.ai_agents import AiAgentPromptRenderable, AIAgent
from relentity.components import Component


class Position(AiAgentPromptRenderable, Component):
    x: float
    y: float

    async def render(self, agent: AIAgent):
        return f"Current Position: {self.x}, {self.y}"
