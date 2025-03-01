from typing import Annotated

from pydantic import PrivateAttr

from relentity.ai.pydantic_ollama.tools import ToolDefinition, tools_to_schema
from relentity.core import Component


class AIDriven(Component):
    """Entities that include this component are driven by an AI agent."""
    model: str
    update_interval: int = 1
    _update_count: int = PrivateAttr(default=0)


class PromptRenderableComponent(Component):
    """Components that implement this mixin can contribute to the prompt for an AI agent."""

    async def render_prompt(self) -> str:
        raise NotImplementedError


class SystemPromptRenderableComponent(Component):
    """Components that implement this mixin can contribute to the system prompt for an AI agent."""

    async def render_system_prompt(self) -> str:
        raise NotImplementedError


class ToolEnabledComponent(Component):
    """
    Components with this mixin can expose tools to the AI system via the @tool decorator.

    The tools are exposed as a dictionary of tool names to tool definitions in the _tools attribute.
    """
    _tools: Annotated[dict[str, ToolDefinition], PrivateAttr()] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tools = {}
        for key, value in self.__class__.__dict__.items():
            if callable(value) and hasattr(value, "_is_tool"):
                tools[key] = getattr(self, key)
        self._tools = tools_to_schema(tools)
