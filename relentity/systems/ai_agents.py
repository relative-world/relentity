from relentity.components.ai_agents import AIAgent, AiAgentPromptRenderable, AIAgentSystemPromptRenderable
from relentity.components.tools import TooledMixin
from relentity.pydantic_ollama.client import PydanticOllamaClient
from relentity.pydantic_ollama.responses import BasicResponse
from relentity.registry import Registry
from relentity.settings import settings
from relentity.systems.base import System
from relentity.pydantic_ollama.tools import wrap_with_actor


class AiAgentSystem(System):

    def __init__(self, registry: Registry):
        super().__init__(registry)
        self._client = PydanticOllamaClient(settings.base_url, settings.default_model)

    async def update(self):
        async for entity in self.registry.entities_with_components(AIAgent):
            system_prompt = []
            prompt = []
            tools = {}

            for component_type, component in entity.components.items():
                if issubclass(component_type, TooledMixin):
                    tools.update(component._tools)
                if issubclass(component_type, AiAgentPromptRenderable):
                    prompt.append(await component.render(entity))
                if issubclass(component_type, AIAgentSystemPromptRenderable):
                    system_prompt.append(await component.render(entity))

            prompt = "\n".join(prompt)
            system_prompt = "\n".join(system_prompt)

            _tools = {}
            for k, v in tools.items():
                _v = v.copy()
                _v._callable = wrap_with_actor(v._callable, actor=entity)
                _tools[k] = _v
            tools = _tools
            _, response = await self._client.generate(
                prompt=prompt,
                system=system_prompt,
                response_model=BasicResponse,
                tools=tools,
            )
            return response
            _, response = await self._get_response(system_prompt, "\n".join(context), tools=tools)
