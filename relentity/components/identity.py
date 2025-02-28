from relentity.components.ai_agents import AiAgentPromptRenderable, AIAgent
from relentity.components import Component


class Identity(Component, AiAgentPromptRenderable):
    name: str
    description: str

    async def render(self, agent: AIAgent):
        return (f"Your name is {self.name}.\n"
                f"{self.name}'s description: {self.description}")
