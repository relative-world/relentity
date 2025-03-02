import pytest

from relentity.ai.components import AIDriven, TextPromptComponent, TextSystemPromptComponent, ToolEnabledComponent
from relentity.ai.pydantic_ollama.tools import tool


@pytest.fixture
def ai_driven_component():
    return AIDriven(model="test_model")


@pytest.fixture
def text_prompt_component():
    return TextPromptComponent(text="Test prompt")


@pytest.fixture
def text_system_prompt_component():
    return TextSystemPromptComponent(text="Test system prompt")


@pytest.fixture
def tool_enabled_component():
    class TestToolComponent(ToolEnabledComponent):
        @tool
        async def test_tool(self):
            return "Tool result"

    return TestToolComponent()


def test_append_prompt(ai_driven_component):
    ai_driven_component.append_prompt("New prompt")
    assert ai_driven_component._prompt_queue == ["New prompt"]


def test_set_prompt(ai_driven_component):
    ai_driven_component.set_prompt("New prompt")
    assert ai_driven_component._prompt_queue == ["New prompt"]


def test_append_system_prompt(ai_driven_component):
    ai_driven_component.append_system_prompt("New system prompt")
    assert ai_driven_component._system_prompt_queue == ["New system prompt"]


def test_set_system_prompt(ai_driven_component):
    ai_driven_component.set_system_prompt("New system prompt")
    assert ai_driven_component._system_prompt_queue == ["New system prompt"]


@pytest.mark.asyncio
async def test_add_event_for_consideration(ai_driven_component):
    await ai_driven_component.add_event_for_consideration("event_type", "event")
    assert ai_driven_component._ai_event_queue == [["event_type", "event"]]


@pytest.mark.asyncio
async def test_render_prompt(ai_driven_component):
    ai_driven_component.append_prompt("Prompt 1")
    ai_driven_component.append_prompt("Prompt 2")
    result = await ai_driven_component.render_prompt(clear=True)
    assert result == "Prompt 1\nPrompt 2\n"
    assert ai_driven_component._prompt_queue == []


@pytest.mark.asyncio
async def test_render_system_prompt(ai_driven_component):
    ai_driven_component.append_system_prompt("System prompt 1")
    ai_driven_component.append_system_prompt("System prompt 2")
    result = await ai_driven_component.render_system_prompt(clear=True)
    assert "System prompt 1" in result
    assert "System prompt 2" in result
    assert ai_driven_component._system_prompt_queue == []


@pytest.mark.asyncio
async def test_text_prompt_component(text_prompt_component):
    result = await text_prompt_component.render_prompt()
    assert result == "Test prompt"


@pytest.mark.asyncio
async def test_text_system_prompt_component(text_system_prompt_component):
    result = await text_system_prompt_component.render_system_prompt()
    assert result == "Test system prompt"


@pytest.mark.asyncio
async def test_tool_enabled_component(tool_enabled_component):
    result = await tool_enabled_component.test_tool()
    assert result == "Tool result"
