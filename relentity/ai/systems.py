import asyncio

from relentity.ai.components import AIDriven, ToolEnabledComponent, PromptRenderableComponent, \
    SystemPromptRenderableComponent
from relentity.ai.events import AI_RESPONSE_EVENT_TYPE
from relentity.ai.pydantic_ollama.client import PydanticOllamaClient
from relentity.ai.pydantic_ollama.responses import BasicResponse
from relentity.ai.pydantic_ollama.tools import wrap_with_actor
from relentity.core import Registry, System, Identity
from relentity.settings import settings
from relentity.spatial import Position, Velocity


async def render_basic_information(entity):
    identity = await entity.get_component(Identity)
    position = await entity.get_component(Position)
    velocity = await entity.get_component(Velocity)

    return (f"Name: {identity.name}\nDescription: {identity.description}\n"
            f"Position: ({position.x}, {position.y})\nVelocity: ({velocity.vx}, {velocity.vy})")


class AIDrivenSystem(System):
    def __init__(self, registry: Registry):
        super().__init__(registry)
        self._client = PydanticOllamaClient(settings.base_url, settings.default_model)

    async def update(self):
        tasks = []
        async for entity in self.registry.entities_with_components(AIDriven):
            tasks.append(self.process_entity(entity))
        await asyncio.gather(*tasks)

    async def process_entity(self, entity):
        ai_driven_component = await entity.get_component(AIDriven)
        ai_driven_component._update_count += 1

        if ai_driven_component._update_count % ai_driven_component.update_interval != 0:
            return  # Skip processing this entity

        system_prompt = []
        prompt = []
        tools = {}

        system_prompt.append(await render_basic_information(entity))
        for component_type, component in entity.components.items():
            if issubclass(component_type, ToolEnabledComponent):
                tools.update(component._tools)
            if issubclass(component_type, PromptRenderableComponent):
                prompt.append(await component.render_prompt())
            if issubclass(component_type, SystemPromptRenderableComponent):
                system_prompt.append(await component.render_system_prompt())

        if hasattr(entity, 'render_system_prompt'):
            system_prompt.append(await entity.render_system_prompt())

        if hasattr(entity, 'render_prompt'):
            prompt.append(await entity.render_prompt())

        prompt_str = "\n".join(prompt) or "<No input this round>"
        system_prompt_str = "\n".join(system_prompt)

        tools = {
            k: v.copy(update={'_callable': wrap_with_actor(v._callable, actor=entity)})
            for k, v in tools.items()
        }

        _, response = await self._client.generate(
            prompt=prompt_str,
            system=system_prompt_str,
            response_model=BasicResponse,
            tools=tools,
        )
        if tools:
            response = response.response
        if response:
            await entity.event_bus.emit(AI_RESPONSE_EVENT_TYPE, response)
        return response
