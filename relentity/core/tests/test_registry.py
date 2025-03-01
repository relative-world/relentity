import pytest

from relentity.spatial import Velocity, Position


@pytest.mark.asyncio
async def test_register_entity(registry, entity):
    """Test registering an entity in the registry."""
    # Arrange - already done by fixtures

    # Act - registry.register_entity is called in entity.__init__

    # Assert
    assert entity in registry.entities


@pytest.mark.asyncio
async def test_entities_with_components(registry, entity_with_components):
    """Test querying entities with specific components."""
    entities_with_pos = [e async for e in registry.entities_with_components(Position)]
    entities_with_pos_vel = [e async for e in registry.entities_with_components(Position, Velocity)]
    assert entity_with_components in entities_with_pos
    assert entity_with_components in entities_with_pos_vel


@pytest.mark.asyncio
async def test_remove_component_from_entity(registry, entity_with_components):
    """Test removing a component from an entity in the registry."""
    await registry.remove_component_from_entity(entity_with_components, Velocity)
    assert Velocity not in entity_with_components.components
