import pytest
import asyncio
from unittest.mock import AsyncMock
from relentity.core.event_bus import EventBus
from relentity.core.exceptions import InvalidEventNameException, InvalidEventPatternException


@pytest.mark.asyncio
async def test_register_and_emit(event_bus):
    """Test registering a handler and emitting an event."""
    # Arrange
    handler = AsyncMock()
    event_bus.register_handler("test.event", handler)
    test_data = {"value": 42}

    # Act
    await event_bus.emit("test.event", test_data)

    # Assert
    handler.assert_awaited_once_with(test_data)


@pytest.mark.asyncio
async def test_wildcard_pattern(event_bus):
    """Test wildcard pattern matching for events."""
    # Arrange
    handler = AsyncMock()
    event_bus.register_handler("test.*", handler)

    # Act
    await event_bus.emit("test.specific", "data")

    # Assert
    handler.assert_awaited_once_with("data")


@pytest.mark.asyncio
async def test_invalid_event_name(event_bus):
    """Test validation of event names."""
    # Arrange & Act & Assert
    with pytest.raises(InvalidEventNameException):
        await event_bus.emit("invalid-event-name")


@pytest.mark.asyncio
async def test_invalid_event_pattern(event_bus):
    """Test validation of event patterns."""
    # Arrange & Act & Assert
    with pytest.raises(InvalidEventPatternException):
        event_bus.register_handler("invalid-pattern", AsyncMock())


@pytest.mark.asyncio
async def test_multiple_handlers(event_bus):
    """Test multiple handlers for the same event."""
    # Arrange
    handler1 = AsyncMock()
    handler2 = AsyncMock()
    event_bus.register_handler("test.event", handler1)
    event_bus.register_handler("test.event", handler2)

    # Act
    await event_bus.emit("test.event", "data")

    # Assert
    handler1.assert_awaited_once_with("data")
    handler2.assert_awaited_once_with("data")
