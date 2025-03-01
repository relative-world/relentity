from typing import Annotated, Any

from pydantic import PrivateAttr

from relentity.ai.pydantic_ollama.tools import ToolDefinition, tools_to_schema
from relentity.ai.utils import pretty_print_event
from relentity.core import Component


class AIDriven(Component):
    """Entities that include this component are driven by an AI agent."""
    model: str
    update_interval: int = 1
    _update_count: int = PrivateAttr(default=0)
    _ai_event_queue: Annotated[list[tuple[str, Any]], PrivateAttr()] = []
    _ai_event_history: Annotated[list[str], PrivateAttr()] = []
    _hashed_event_queue: Annotated[dict[str, tuple[str, Any]], PrivateAttr()] = {}
    _hashed_event_history: Annotated[dict[str, tuple[str, Any]], PrivateAttr()] = {}
    _prompt_queue: Annotated[list[str], PrivateAttr()] = []
    _system_prompt_queue: Annotated[list[str], PrivateAttr()] = []

    def append_prompt(self, content):
        self._prompt_queue.append(content)

    def set_prompt(self, content: str):
        self._prompt_queue = [content]

    def append_system_prompt(self, content: str):
        self._system_prompt_queue.append(content)

    def set_system_prompt(self, content: str):
        self._system_prompt_queue = [content]

    async def add_event_for_consideration(self, event_type, event, hash_key=None):
        if hash_key is not None:
            _hash_key = f"{event_type}{hash_key}"
            self._hashed_event_queue[_hash_key] = (event_type, event)
            for existing_event_type, existing_event in self._ai_event_queue:
                if existing_event_type == event_type and hash_key == id(existing_event):
                    return
        else:
            self._ai_event_queue.append([event_type, event])

    async def render_prompt(self, clear=False):
        hashed_rendered_events = []
        _hash_event_queue, self._hashed_event_queue = self._hashed_event_queue, {}
        for _hash_key, (event_type, event) in _hash_event_queue.items():
            hashed_rendered_events.append(await pretty_print_event(event_type, event))
            self._hashed_event_history[_hash_key] = (event_type, event)

        _ai_event_queue, self._ai_event_queue = self._ai_event_queue, []
        unhashed_rendered_events = [await pretty_print_event(*payload) for payload in _ai_event_queue]

        self._ai_event_history.extend(unhashed_rendered_events)

        output = self._prompt_queue
        if clear:
            self._prompt_queue = []
        return "\n".join(output) + "\n".join(unhashed_rendered_events) + "\n" + "\n".join(hashed_rendered_events)

    async def render_system_prompt(self, clear=False):
        rendered_events = []
        for _hash_key, (event_type, event) in self._hashed_event_history.items():
            if _hash_key in self._hashed_event_queue:
                continue
            rendered_events.append(await pretty_print_event(event_type, event, past_tense=True))

        output = self._system_prompt_queue
        if clear:
            self._system_prompt_queue = []
        return ("\n".join(output) +
                "\n100 most recent events:" + "\n".join(self._ai_event_history[-100::]) +
                "\ndistinct memories" + "\n".join(rendered_events))


class PromptRenderableComponent(Component):
    """Components that implement this mixin can contribute to the prompt for an AI agent."""

    async def render_prompt(self) -> str:
        raise NotImplementedError


class TextPromptComponent(PromptRenderableComponent):
    text: str

    async def render_prompt(self) -> str:
        return self.text


class SystemPromptRenderableComponent(Component):
    """Components that implement this mixin can contribute to the system prompt for an AI agent."""

    async def render_system_prompt(self) -> str:
        raise NotImplementedError


class TextSystemPromptComponent(SystemPromptRenderableComponent):
    text: str

    async def render_system_prompt(self) -> str:
        return self.text


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
