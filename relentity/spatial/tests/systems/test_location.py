from unittest.mock import AsyncMock

import pytest

from relentity.core import EntityRef
from relentity.core.entities import Entity
from relentity.spatial.registry import SpatialRegistry
from relentity.spatial.components import Position, Area, Located
from relentity.spatial.events import AREA_ENTERED_EVENT_TYPE, AREA_EXITED_EVENT_TYPE
from relentity.spatial.systems import LocationSystem


@pytest.fixture
def registry():
    return SpatialRegistry()


@pytest.fixture
def location_system(registry):
    return LocationSystem(registry)


@pytest.mark.asyncio
async def test_entity_enters_area(registry, location_system):
    # Create area entity
    area_entity = Entity[Area(center_point=(0, 0), geometry=[(0, 0), (10, 0), (10, 10), (0, 10)])](registry)

    # Create entity within area
    entity = Entity[Position(x=5, y=5)](registry)

    mock_entity_area_entered_handler = AsyncMock()
    mock_area_area_entered_handler = AsyncMock()

    entity.event_bus.register_handler(AREA_ENTERED_EVENT_TYPE, mock_entity_area_entered_handler)
    area_entity.event_bus.register_handler(AREA_ENTERED_EVENT_TYPE, mock_area_area_entered_handler)

    # Update the system
    await location_system.update()

    # Verify the entity has the Located component
    located = await entity.get_component(Located)
    assert located.area_entity_ref.entity_id == area_entity.id

    # validate that our event handlers were called
    mock_area_area_entered_handler.assert_awaited_once()
    mock_entity_area_entered_handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_entity_exits_area(registry, location_system):
    # Create area entity
    area_entity = Entity[Area(center_point=(0, 0), geometry=[(0, 0), (10, 0), (10, 10), (0, 10)])](registry)
    area_entity_ref = EntityRef(entity_id=area_entity.id, _registry=registry)

    # Create entity within area
    entity = Entity[Position(x=5, y=5), Located(area_entity_ref=area_entity_ref)](registry)

    mock_entity_area_entered_handler = AsyncMock()
    mock_entity_area_exited_handler = AsyncMock()
    entity.event_bus.register_handler(AREA_ENTERED_EVENT_TYPE, mock_entity_area_entered_handler)
    entity.event_bus.register_handler(AREA_EXITED_EVENT_TYPE, mock_entity_area_exited_handler)

    mock_area_area_entered_handler = AsyncMock()
    mock_area_area_exited_handler = AsyncMock()
    area_entity.event_bus.register_handler(AREA_ENTERED_EVENT_TYPE, mock_area_area_entered_handler)
    area_entity.event_bus.register_handler(AREA_EXITED_EVENT_TYPE, mock_area_area_exited_handler)

    # Update the system once, cause you gotta be in an area to leave it.
    await location_system.update()

    assert mock_entity_area_entered_handler.awaited_once()
    assert mock_area_area_entered_handler.awaited_once()

    # Move entity outside the area
    position = await entity.get_component(Position)
    position.x = 15
    position.y = 15

    # Update the system
    await location_system.update()

    located = await entity.get_component(Located)
    assert located is None

    # enter wasn't called again
    assert mock_entity_area_entered_handler.awaited_once()
    assert mock_area_area_entered_handler.awaited_once()

    # exit was called once each
    assert mock_area_area_exited_handler.awaited_once()
    assert mock_entity_area_exited_handler.awaited_once()


@pytest.mark.asyncio
async def test_entity_moves_within_area(registry, location_system):
    # Create area entity
    area_entity = Entity[Area(center_point=(0, 0), geometry=[(0, 0), (10, 0), (10, 10), (0, 10)])](registry)
    area_entity_ref = EntityRef(entity_id=area_entity.id, _registry=registry)

    # Create entity within area
    entity = Entity[Position(x=5, y=5), Located(area_entity_ref=area_entity_ref)](registry)

    mock_entity_area_entered_handler = AsyncMock()
    mock_entity_area_exited_handler = AsyncMock()
    entity.event_bus.register_handler(AREA_ENTERED_EVENT_TYPE, mock_entity_area_entered_handler)
    entity.event_bus.register_handler(AREA_EXITED_EVENT_TYPE, mock_entity_area_exited_handler)

    mock_area_area_entered_handler = AsyncMock()
    mock_area_area_exited_handler = AsyncMock()
    area_entity.event_bus.register_handler(AREA_ENTERED_EVENT_TYPE, mock_area_area_entered_handler)
    area_entity.event_bus.register_handler(AREA_EXITED_EVENT_TYPE, mock_area_area_exited_handler)

    # Update the system once, cause you gotta be in an area to leave it.
    await location_system.update()

    assert mock_entity_area_entered_handler.awaited_once()
    assert mock_area_area_entered_handler.awaited_once()

    # Move entity within the area
    position = await entity.get_component(Position)
    position.x = 7
    position.y = 7

    # Update the system
    await location_system.update()

    # Verify the entity still has the Located component
    located = await entity.get_component(Located)
    assert located.area_entity_ref.entity_id == area_entity.id

    # enter wasn't called again
    assert mock_entity_area_entered_handler.awaited_once()
    assert mock_area_area_entered_handler.awaited_once()

    # exit was never called
    mock_area_area_exited_handler.assert_not_awaited()
    mock_entity_area_exited_handler.assert_not_awaited()
