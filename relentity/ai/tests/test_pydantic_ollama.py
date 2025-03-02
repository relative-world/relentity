from unittest.mock import AsyncMock, MagicMock, patch

import orjson
import pytest
from pydantic import BaseModel

from relentity.ai.pydantic_ollama.client import PydanticOllamaClient, ollama_generate
from relentity.ai.pydantic_ollama.exceptions import UnparsableResponseError
from relentity.ai.pydantic_ollama.json import (
    maybe_parse_json, fix_json_response, inline_json_schema_defs
)
from relentity.ai.pydantic_ollama.responses import BasicResponse, TooledResponse
from relentity.ai.pydantic_ollama.tools import (
    ToolCallRequest, ToolCallResponse, tool,
    tools_to_schema, function_to_schema, call_tool, wrap_with_actor, ToolDefinition
)


class TestJsonFunctions:
    def test_maybe_parse_json_valid(self):
        valid_json = '{"text": "Hello world"}'
        result = maybe_parse_json(valid_json)
        assert result == {"text": "Hello world"}

    def test_maybe_parse_json_markdown_wrapped(self):
        markdown_json = '```json\n{"text": "Hello world"}\n```'
        result = maybe_parse_json(markdown_json)
        assert result == {"text": "Hello world"}

    def test_maybe_parse_json_invalid(self):
        invalid_json = '{"text": "Hello world'
        with pytest.raises(orjson.JSONDecodeError):
            maybe_parse_json(invalid_json)

    def test_inline_json_schema_defs(self):
        schema = {
            "type": "object",
            "properties": {
                "foo": {"$ref": "#/$defs/bar"}
            },
            "$defs": {
                "bar": {"type": "string"}
            }
        }
        expected = {
            "type": "object",
            "properties": {
                "foo": {"type": "string"}
            }
        }
        result = inline_json_schema_defs(schema)
        assert result == expected


class TestPydanticOllamaClient:
    @pytest.fixture
    def client(self):
        with patch('relentity.ai.pydantic_ollama.client.AsyncOllamaClient') as mock_client:
            client = PydanticOllamaClient("http://localhost:11434", "llama2")
            client._client = AsyncMock()
            yield client

    @patch('relentity.ai.pydantic_ollama.client.ollama_generate')
    async def test_generate_basic_response(self, mock_generate, client):
        mock_response = MagicMock()
        mock_response.response = '{"text": "Hello World"}'
        mock_generate.return_value = mock_response

        response, response_obj = await client.generate(
            prompt="Hello",
            system="You are a helpful assistant",
            response_model=BasicResponse
        )

        assert response_obj.text == "Hello World"
        mock_generate.assert_called_once()

    @patch('relentity.ai.pydantic_ollama.client.ollama_generate')
    async def test_generate_invalid_json(self, mock_generate, client):
        mock_response = MagicMock()
        mock_response.response = 'Invalid JSON'
        mock_generate.return_value = mock_response

        with patch('relentity.ai.pydantic_ollama.client.fix_json_response') as mock_fix:
            mock_fix.return_value = {"text": "Fixed response"}
            _, response_obj = await client.generate(
                prompt="Hello",
                system="You are a helpful assistant",
                response_model=BasicResponse
            )
            assert response_obj.text == "Fixed response"

    @patch('relentity.ai.pydantic_ollama.client.ollama_generate')
    async def test_generate_with_tools(self, mock_generate, client):
        mock_response = MagicMock()
        mock_response.response = '{"tool_call": {"function_name": "test_tool", "function_args": {"arg1": "value"}}}'
        mock_generate.return_value = mock_response

        tool_def = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"arg1": {"type": "string"}},
            _callable=AsyncMock(return_value="Tool result")
        )
        tools = {"test_tool": tool_def}

        with patch('relentity.ai.pydantic_ollama.client.call_tool') as mock_call_tool:
            mock_call_tool.return_value = ToolCallResponse(
                tool_call=ToolCallRequest(function_name="test_tool", function_args={"arg1": "value"}),
                result="Tool result"
            )

            _, response_obj = await client.generate(
                prompt="Hello",
                system="You are a helpful assistant",
                response_model=BasicResponse,
                tools=tools
            )

            assert isinstance(response_obj, TooledResponse)
            mock_call_tool.assert_called_once()


class TestToolFunctions:
    def test_tool_decorator(self):
        @tool
        def test_function():
            """Test function"""
            return "result"

        assert hasattr(test_function, "_is_tool")
        assert test_function._is_tool is True

    def test_function_to_schema(self):
        def test_function(param1: str, param2: int = 0):
            """Test function description"""
            return f"{param1} {param2}"

        schema = function_to_schema(test_function)

        assert schema.function.name == "test_function"
        assert schema.function.description == "Test function description"
        assert "param1" in schema.function.parameters
        assert "param2" in schema.function.parameters
        assert schema.function.parameters["param1"]["type"] == "string"
        assert schema.function.parameters["param2"]["type"] == "integer"
        assert schema.function.required == ["param1"]

    def test_tools_to_schema(self):
        @tool
        def test_function1(param: str):
            """Test function 1"""
            return param

        @tool
        def test_function2(param: int):
            """Test function 2"""
            return param

        tools = {"func1": test_function1, "func2": test_function2}
        schema = tools_to_schema(tools)

        assert len(schema) == 2
        assert "func1" in schema
        assert "func2" in schema
        assert schema["func1"].function.name == "test_function1"
        assert schema["func2"].function.name == "test_function2"

    async def test_call_tool(self):
        async def test_function(arg1: str):
            return f"Result: {arg1}"

        tool_def = MagicMock()
        tool_def._callable = test_function
        tools = {"test_tool": tool_def}

        tool_call = ToolCallRequest(function_name="test_tool", function_args={"arg1": "test"})
        result = await call_tool(tools, tool_call)

        assert result.result == "Result: test"
        assert result.tool_call == tool_call

    def test_wrap_with_actor(self):
        def test_function(self, actor, arg1):
            return f"Self: {self}, Actor: {actor}, Arg: {arg1}"

        mock_self = "self_obj"
        mock_actor = "actor_obj"

        wrapped = wrap_with_actor(test_function, mock_actor)
        result = wrapped(mock_self, "test_arg")

        assert result == f"Self: {mock_self}, Actor: {mock_actor}, Arg: test_arg"


class TestResponseModels:
    def test_basic_response(self):
        data = {"text": "Hello world"}
        response = BasicResponse.model_validate(data)
        assert response.text == "Hello world"

    def test_tooled_response(self):
        # Test with response only
        data = {"response": {"text": "Hello world"}}
        response = TooledResponse[BasicResponse].model_validate(data)
        assert response.response.text == "Hello world"
        assert response.tool_call is None

        # Test with tool call only
        data = {
            "tool_call": {
                "function_name": "test_tool",
                "function_args": {"arg1": "value"}
            }
        }
        response = TooledResponse[BasicResponse].model_validate(data)
        assert response.response is None
        assert response.tool_call.function_name == "test_tool"
        assert response.tool_call.function_args == {"arg1": "value"}


class TestFixJsonResponse:
    @patch('relentity.ai.pydantic_ollama.json.orjson.dumps')
    async def test_fix_json_response(self, mock_dumps):
        mock_dumps.return_value = b'{"type":"object","properties":{"text":{"type":"string"}}}'

        client_mock = AsyncMock()
        mock_response = MagicMock()
        mock_response.response = '{"text": "Fixed text"}'
        client_mock.generate.return_value = mock_response

        class TestModel(BaseModel):
            text: str

        result = await fix_json_response(client_mock, 'broken json', TestModel)

        assert result == {"text": "Fixed text"}
        client_mock.generate.assert_called_once()

    @patch('relentity.ai.pydantic_ollama.json.orjson.dumps')
    async def test_fix_json_response_failure(self, mock_dumps):
        mock_dumps.return_value = b'{}'

        client_mock = AsyncMock()
        mock_response = MagicMock()
        mock_response.response = 'still broken'
        client_mock.generate.return_value = mock_response

        class TestModel(BaseModel):
            text: str

        with pytest.raises(UnparsableResponseError):
            await fix_json_response(client_mock, 'broken json', TestModel)


class TestOllamaGenerate:
    async def test_ollama_generate(self):
        client_mock = AsyncMock()
        client_mock.generate.return_value = MagicMock(response="Test response")

        with patch('relentity.ai.pydantic_ollama.client.settings') as mock_settings:
            mock_settings.model_keep_alive = "5m"

            response = await ollama_generate(
                client=client_mock,
                model="test-model",
                prompt="Hello",
                system="You are a test",
                context=[1, 2, 3]
            )

            client_mock.generate.assert_called_once_with(
                model="test-model",
                prompt="Hello",
                system="You are a test",
                context=[1, 2, 3],
                keep_alive="5m"
            )
            assert response.response == "Test response"
