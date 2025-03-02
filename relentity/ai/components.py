from typing import Annotated, Any

from pydantic import PrivateAttr

from relentity.ai.pydantic_ollama.tools import ToolDefinition, tools_to_schema
from relentity.ai.utils import pretty_print_event
from relentity.core import Component


class AIDriven(Component):
    """
    Component for entities driven by an AI agent.

    Attributes:
        model (str): The AI model used to drive the entity.
        update_interval (int): The interval at which the AI updates.
        _update_count (int): Internal counter for updates.
        _ai_event_queue (list[tuple[str, Any]]): Queue of events for the AI to consider.
        _ai_event_history (list[str]): History of events considered by the AI.
        _hashed_event_queue (dict[str, tuple[str, Any]]): Hashed queue of events for the AI to consider.
        _hashed_event_history (dict[str, tuple[str, Any]]): Hashed history of events considered by the AI.
        _prompt_queue (list[str]): Queue of prompts for the AI.
        _system_prompt_queue (list[str]): Queue of system prompts for the AI.
    """

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
        """
        Appends a prompt to the AI's prompt queue.

        Args:
            content (str): The content to append to the prompt queue.
        """
        self._prompt_queue.append(content)

    def set_prompt(self, content: str):
        """
        Sets the AI's prompt queue to a single prompt.

        Args:
            content (str): The content to set as the prompt.
        """
        self._prompt_queue = [content]

    def append_system_prompt(self, content: str):
        """
        Appends a system prompt to the AI's system prompt queue.

        Args:
            content (str): The content to append to the system prompt queue.
        """
        self._system_prompt_queue.append(content)

    def set_system_prompt(self, content: str):
        """
        Sets the AI's system prompt queue to a single system prompt.

        Args:
            content (str): The content to set as the system prompt.
        """
        self._system_prompt_queue = [content]

    async def add_event_for_consideration(self, event_type, event, hash_key=None):
        """
        Adds an event for the AI to consider.

        Args:
            event_type (str): The type of the event.
            event (Any): The event data.
            hash_key (str, optional): A key to hash the event. Defaults to None.
        """
        if hash_key is not None:
            _hash_key = f"{event_type}{hash_key}"
            self._hashed_event_queue[_hash_key] = (event_type, event)
            for existing_event_type, existing_event in self._ai_event_queue:
                if existing_event_type == event_type and hash_key == id(existing_event):
                    return
        else:
            self._ai_event_queue.append([event_type, event])

    async def render_prompt(self, clear=False):
        """
        Renders the AI's prompt.

        Args:
            clear (bool, optional): Whether to clear the prompt queue after rendering. Defaults to False.

        Returns:
            str: The rendered prompt.
        """
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
        """
        Renders the AI's system prompt.

        Args:
            clear (bool, optional): Whether to clear the system prompt queue after rendering. Defaults to False.

        Returns:
            str: The rendered system prompt.
        """
        rendered_events = []
        for _hash_key, (event_type, event) in self._hashed_event_history.items():
            if _hash_key in self._hashed_event_queue:
                continue
            rendered_events.append(await pretty_print_event(event_type, event, past_tense=True))

        output = self._system_prompt_queue
        if clear:
            self._system_prompt_queue = []
        return (
            "\n".join(output)
            + "\n100 most recent events:"
            + "\n".join(self._ai_event_history[-100::])
            + "\ndistinct memories"
            + "\n".join(rendered_events)
        )


class PromptRenderableComponent(Component):
    """
    Mixin for components that can contribute to the AI's prompt.
    """

    async def render_prompt(self) -> str:
        """
        Renders the component's contribution to the AI's prompt.

        Returns:
            str: The rendered prompt.
        """
        raise NotImplementedError


class TextPromptComponent(PromptRenderableComponent):
    """
    Component for adding text to the AI's prompt.

    Attributes:
        text (str): The text to add to the prompt.
    """

    text: str

    async def render_prompt(self) -> str:
        """
        Renders the text prompt.

        Returns:
            str: The text prompt.
        """
        return self.text


class SystemPromptRenderableComponent(Component):
    """
    Mixin for components that can contribute to the AI's system prompt.
    """

    async def render_system_prompt(self) -> str:
        """
        Renders the component's contribution to the AI's system prompt.

        Returns:
            str: The rendered system prompt.
        """
        raise NotImplementedError


class TextSystemPromptComponent(SystemPromptRenderableComponent):
    """
    Component for adding text to the AI's system prompt.

    Attributes:
        text (str): The text to add to the system prompt.
    """

    text: str

    async def render_system_prompt(self) -> str:
        """
        Renders the text system prompt.

        Returns:
            str: The text system prompt.
        """
        return self.text


class ToolEnabledComponent(Component):
    """
    Mixin for components that expose tools to the AI system via the @tool decorator.

    Attributes:
        _tools (dict[str, ToolDefinition]): Dictionary of tool names to tool definitions.
    """

    _tools: Annotated[dict[str, ToolDefinition], PrivateAttr()] = {}

    def __init__(self, *args, **kwargs):
        """
        Initializes the ToolEnabledComponent and registers tools.
        """
        super().__init__(*args, **kwargs)
        tools = {}
        for key, value in self.__class__.__dict__.items():
            if callable(value) and hasattr(value, "_is_tool"):
                tools[key] = getattr(self, key)
        self._tools = tools_to_schema(tools)
