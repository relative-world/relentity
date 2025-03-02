import pytest

from relentity.core import Entity
from relentity.spatial import Velocity, Position


@pytest.mark.asyncio
async def test_register_entity(registry):
    """Test registering an entity in the registry."""
    entity = Entity(registry)
    assert entity in registry.entities


@pytest.mark.asyncio
async def test_entities_with_components(registry):
    """Test querying entities with specific components."""
    entity = Entity[
        Position(x=10, y=10),
        Velocity(vx=5, vy=5)
    ](registry)

    entities_with_pos = [e async for e in registry.entities_with_components(Position)]
    entities_with_pos_vel = [e async for e in registry.entities_with_components(Position, Velocity)]
    assert entity in entities_with_pos
    assert entity in entities_with_pos_vel


@pytest.mark.asyncio
async def test_remove_component_from_entity(registry):
    """Test removing a component from an entity in the registry."""
    entity = Entity[
        Position(x=10, y=10),
        Velocity(vx=5, vy=5)
    ](registry)

    await registry.remove_component_from_entity(entity, Velocity)
    assert Velocity not in entity.components
