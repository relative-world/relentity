import pytest
from unittest.mock import AsyncMock

from relentity.core.entities import Entity
from relentity.spatial.registry import SpatialRegistry
from relentity.spatial.components import Position, Velocity, Vision, Visible
from relentity.spatial.events import EntitySeenEvent, ENTITY_SEEN_EVENT_TYPE
from relentity.spatial.systems import VisionSystem


@pytest.fixture
def registry():
    return SpatialRegistry()


@pytest.fixture
def vision_system(registry):
    return VisionSystem(registry)


@pytest.mark.asyncio
async def test_entity_sees_visible_entity_within_range(registry, vision_system):
    # Create entity with vision
    observer_entity = Entity[Position(x=0, y=0), Vision(max_range=100)](registry)

    # Create a visible entity within range
    visible_entity = Entity[Position(x=50, y=0), Velocity(vx=5, vy=0), Visible()](registry)

    # Mock the emit method to track calls
    observer_entity.event_bus.emit = AsyncMock()

    # Update the system
    await vision_system.update()

    # Verify that ENTITY_SEEN_EVENT_TYPE was emitted with the visible entity info
    observer_entity.event_bus.emit.assert_called_once()
    args = observer_entity.event_bus.emit.call_args[0]
    assert args[0] == ENTITY_SEEN_EVENT_TYPE
    assert isinstance(args[1], EntitySeenEvent)
    assert args[1].entity_ref.entity_id == visible_entity.id
    assert args[1].position.x == 50 and args[1].position.y == 0
    assert args[1].velocity.vx == 5 and args[1].velocity.vy == 0


@pytest.mark.asyncio
async def test_entity_does_not_see_outside_vision_range(registry, vision_system):
    # Create entity with limited vision range
    observer_entity = Entity[Position(x=0, y=0), Vision(max_range=50)](registry)

    # Create a visible entity outside the vision range
    Entity[Position(x=60, y=0), Visible()](registry)  # Distance = 60 > 50

    # Mock the emit method to track calls
    observer_entity.event_bus.emit = AsyncMock()

    # Update the system
    await vision_system.update()

    # Verify that no events were emitted (entity is out of range)
    observer_entity.event_bus.emit.assert_not_called()


@pytest.mark.asyncio
async def test_entity_sees_multiple_visible_entities(registry, vision_system):
    # Create entity with vision
    observer_entity = Entity[Position(x=0, y=0), Vision(max_range=100)](registry)

    # Create multiple visible entities at different distances
    visible_entity1 = Entity[Position(x=30, y=0), Velocity(vx=1, vy=0), Visible()](registry)
    visible_entity2 = Entity[Position(x=0, y=70), Velocity(vx=0, vy=2), Visible()](registry)
    visible_entity3 = Entity[Position(x=110, y=0), Velocity(vx=3, vy=0), Visible()](registry)  # Out of range

    # Mock the emit method to track calls
    observer_entity.event_bus.emit = AsyncMock()

    # Update the system
    await vision_system.update()

    # Verify that events were emitted for the two in-range entities
    assert observer_entity.event_bus.emit.call_count == 2

    # Collect the entities that were seen
    seen_entities = []
    for call in observer_entity.event_bus.emit.call_args_list:
        args = call[0]
        assert args[0] == ENTITY_SEEN_EVENT_TYPE
        seen_entities.append(args[1].entity_ref.entity_id)

    # Verify the right entities were seen
    assert visible_entity1.id in seen_entities
    assert visible_entity2.id in seen_entities
    assert visible_entity3.id not in seen_entities


@pytest.mark.asyncio
async def test_entity_without_vision_component(registry, vision_system):
    # Create entity with only Position but no Vision
    observer_entity = Entity[Position(x=0, y=0)](registry)

    # Create a visible entity
    Entity[Position(x=10, y=0), Visible()](registry)

    # Mock the emit method to track calls
    observer_entity.event_bus.emit = AsyncMock()

    # Update the system
    await vision_system.update()

    # Verify that no events were emitted (entity has no Vision)
    observer_entity.event_bus.emit.assert_not_called()


@pytest.mark.asyncio
async def test_entity_does_not_see_itself(registry, vision_system):
    # Create entity with both Vision and Visible components
    entity = Entity[Position(x=0, y=0), Vision(max_range=100), Visible(), Velocity(vx=0, vy=0)](registry)

    # Mock the emit method to track calls
    entity.event_bus.emit = AsyncMock()

    # Update the system
    await vision_system.update()

    # Verify that no events were emitted (entity shouldn't see itself)
    entity.event_bus.emit.assert_not_called()
