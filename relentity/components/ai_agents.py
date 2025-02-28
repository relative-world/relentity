from relentity.components import Component


class AIAgent(Component):
    model: str


class AiAgentPromptRenderable:

    async def render(self, agent: AIAgent):
        return "<an interactable object>"


class AIAgentSystemPromptRenderable:

    async def render(self, agent: AIAgent):
        return "You are an AI agent in a game. Change direction regularly"


class AIAgentSystemPrompt(AIAgentSystemPromptRenderable, Component): ...