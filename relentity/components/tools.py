from typing import Annotated

from pydantic import PrivateAttr

from relentity.pydantic_ollama.tools import ToolDefinition, tools_to_schema


class TooledMixin:
    _tools: Annotated[dict[str, ToolDefinition], PrivateAttr()] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tools = {}
        for key, value in self.__class__.__dict__.items():
            if callable(value) and hasattr(value, "_is_tool"):
                tools[key] = getattr(self, key)
        self._tools = tools_to_schema(tools)
