import asyncio

from pydantic import BaseModel

from relentity.ai.components import (
    AIDriven,
    ToolEnabledComponent,
    PromptRenderableComponent,
    SystemPromptRenderableComponent,
)
from relentity.ai.events import AI_RESPONSE_EVENT_TYPE
from relentity.ai.pydantic_ollama.client import PydanticOllamaClient
from relentity.ai.pydantic_ollama.tools import wrap_with_actor
from relentity.ai.utils import pretty_name_entity
from relentity.core import Registry, System, Identity
from relentity.settings import settings
from relentity.spatial import Position, Velocity, Located


class EmotiveResponse(BaseModel):
    emotion: str | None = None
    speech: str | None = None
    thought: str | None = None


async def render_basic_information(entity, component_types):
    """
    Renders basic information about an entity based on its components.

    Args:
        entity (Entity): The entity to render information for.
        component_types (list[Type[Component]]): The types of components to include in the information.

    Returns:
        str: The rendered basic information.
    """
    info = []
    for component_type in component_types:
        component = await entity.get_component(component_type)
        if not component:
            continue

        if component_type == Located:
            area_entity = await component.area_entity_ref.resolve()
            area_name = await pretty_name_entity(area_entity)
            info.append(f"Currently located at: {area_name}")
        elif component_type == Identity:
            info.append(
                f'Your characters name is "{component.name}"\nThis is a description of your character: {component.description}'
            )
        elif component_type == Position:
            info.append(f"Position: ({component.x:.2f}, {component.y:.2f})")
        elif component_type == Velocity:
            info.append(f"Velocity: ({component.vx:.2f}, {component.vy:.2f})")
        else:
            info.append(f"{component_type.__name__}: {component}")

    return "\n".join(info)


class AIDrivenSystem(System):
    """
    System for processing entities driven by AI.

    Attributes:
        _client (PydanticOllamaClient): The client for interacting with the AI model.
    """

    def __init__(self, registry: Registry):
        """
        Initializes the AIDrivenSystem with a registry and AI client.

        Args:
            registry (Registry): The registry to be used by the system.
        """
        super().__init__(registry)
        self._client = PydanticOllamaClient(settings.base_url, settings.default_model)
        self._processing_entities = set()

    async def update(self, delta_time: float = 0) -> None:
        """
        Updates the system by processing entities with the AIDriven component
        that are not already being processed.
        """
        async for entity_ref in self.registry.entities_with_components(AIDriven):
            resolved_entity = await entity_ref.resolve()

            # Skip if entity is already being processed
            if resolved_entity.id in self._processing_entities:
                continue

            # Mark entity as being processed
            self._processing_entities.add(resolved_entity.id)

            # Create a task for processing the entity
            task = asyncio.create_task(self.process_entity(resolved_entity))

            # Set up a callback to handle task completion
            task.add_done_callback(lambda t, entity_id=resolved_entity.id: self._handle_task_completion(t, entity_id))

    def _handle_task_completion(self, task, entity_id):
        """
        Handles the completion of an entity processing task.

        Args:
            task (asyncio.Task): The completed task.
            entity_id: The ID of the processed entity.
        """
        # Remove the entity from the processing set
        self._processing_entities.discard(entity_id)

        # Handle any exceptions that occurred during processing
        if not task.cancelled():
            task.result()

    async def process_entity(self, entity):
        """
        Processes an entity with the AIDriven component.

        Args:
            entity (Entity): The entity to process.
        """
        ai_driven_component = await entity.get_component(AIDriven)
        ai_driven_component._update_count += 1

        if ai_driven_component._update_count % ai_driven_component.update_interval != 0:
            return  # Skip processing this entity

        system_prompt = []
        prompt = []
        tools = ai_driven_component.extra_tools

        component_types = [Identity, Position, Velocity, Located]
        system_prompt.append(await render_basic_information(entity, component_types))
        for component_type, component in entity.components.items():
            if issubclass(component_type, ToolEnabledComponent):
                tools.update(component._tools)
            if issubclass(component_type, PromptRenderableComponent):
                prompt.append(await component.render_prompt())
            if issubclass(component_type, SystemPromptRenderableComponent):
                system_prompt.append(await component.render_system_prompt())

        system_prompt.append(await ai_driven_component.render_system_prompt())
        prompt.append(await ai_driven_component.render_prompt())

        prompt_str = "\n".join(prompt) or "<No input this round>"
        system_prompt_str = "\n".join(system_prompt)
        print("\n" + prompt_str)
        print("=" * 80)
        print(system_prompt_str + "\n")

        tools = {k: v.copy(update={"_callable": wrap_with_actor(v._callable, actor=entity)}) for k, v in tools.items()}

        _, response = await self._client.generate(
            prompt=prompt_str,
            system=system_prompt_str,
            response_model=EmotiveResponse,
            tools=tools,
        )
        # if tools:
        #     response = response.response
        if response:
            await entity.event_bus.emit(
                AI_RESPONSE_EVENT_TYPE,
                response,
            )
        return response
