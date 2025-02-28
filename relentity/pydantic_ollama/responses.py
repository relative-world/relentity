from typing import Generic, TypeVar

from pydantic import BaseModel

from relentity.pydantic_ollama.tools import ToolCallRequest


class BasicResponse(BaseModel):
    text: str


DataT = TypeVar('DataT')


class TooledResponse(BaseModel, Generic[DataT]):
    response: DataT | None = None
    tool_call: ToolCallRequest | None = None
