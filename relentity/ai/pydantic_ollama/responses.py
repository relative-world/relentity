from typing import Generic, TypeVar, Any

from pydantic import BaseModel

from .tools import ToolCallRequest


class BasicResponse(BaseModel):
    text: str


DataT = TypeVar("DataT")


class TooledResponse(BaseModel, Generic[DataT]):
    response: DataT | None = None
    tool_call: ToolCallRequest | None = None


class ResolvedTooledResponse(BaseModel, Generic[DataT]):
    response: DataT | None = None
    tool_call: ToolCallRequest | None = None
    tool_call_result: Any = None
