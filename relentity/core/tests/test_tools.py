import pytest
import asyncio
from relentity.ai.pydantic_ollama.tools import (
    tool, call_tool, function_to_schema, tools_to_schema,
    py_type_to_param_type, ToolCallRequest, ToolCallResponse,
    wrap_with_actor
)


def test_py_type_to_param_type():
    """Test conversion of Python types to parameter types."""
    # Arrange & Act & Assert
    assert py_type_to_param_type(str) == "string"
    assert py_type_to_param_type(int) == "integer"
    assert py_type_to_param_type(float) == "number"
    assert py_type_to_param_type(bool) == "boolean"
    assert py_type_to_param_type(list) == "array"
    assert py_type_to_param_type(dict) == "object"
    assert py_type_to_param_type(object) == "string"  # Default case


def test_tool_decorator():
    """Test the tool decorator."""

    # Arrange
    @tool
    def test_function():
        return "result"

    # Act & Assert
    assert hasattr(test_function, "_is_tool")
    assert test_function._is_tool is True


@pytest.mark.asyncio
async def test_function_to_schema():
    """Test converting a function to a schema."""

    # Arrange
    def test_function(arg1: str, arg2: int = 0) -> str:
        """Test function docstring."""
        return arg1 * arg2

    # Act
    schema = function_to_schema(test_function)

    # Assert
    assert schema.function.name == "test_function"
    assert schema.function.description == "Test function docstring."
    assert "arg1" in schema.function.parameters
    assert schema.function.parameters["arg1"]["type"] == "string"
    assert "arg2" in schema.function.parameters
    assert schema.function.required == ["arg1"]
    assert schema._callable == test_function


@pytest.mark.asyncio
async def test_call_tool():
    """Test calling a tool function."""

    # Arrange
    @tool
    async def add(x: int, y: int) -> int:
        return x + y

    tools = {"add": function_to_schema(add)}
    tool_call = ToolCallRequest(function_name="add", function_args={"x": 5, "y": 7})

    # Act
    response = await call_tool(tools, tool_call)

    # Assert
    assert isinstance(response, ToolCallResponse)
    assert response.result == 12
    assert response.tool_call == tool_call


def test_wrap_with_actor():
    """Test wrapping a function with actor parameter."""

    # Arrange
    def original_func(self, actor, param2):
        return f"{self}, {actor}, {param2}"

    actor = "test_actor"

    # Act
    wrapped = wrap_with_actor(original_func, actor)
    result = wrapped("self_value", "param2_value")

    # Assert
    assert result == "self_value, test_actor, param2_value"
