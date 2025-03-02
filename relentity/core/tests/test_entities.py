import pytest

from relentity.core.components import Component, Identity
from relentity.spatial import Position, Velocity


# Use fixtures from conftest.py for registry and entity


@pytest.mark.asyncio
async def test_add_component(entity):
    """Test adding a component to an entity."""
    position = Position(x=10, y=20)

    await entity.add_component(position)
    assert await entity.get_component(Position) == position
    assert position in entity.components.values()


@pytest.mark.asyncio
async def test_get_component(entity_with_components):
    """Test retrieving a component from an entity."""
    assert (await entity_with_components.get_component(Position)).x == 0
    assert (await entity_with_components.get_component(Velocity)).vx == 1
    assert (await entity_with_components.get_component(Identity)).name == "Test Entity"


@pytest.mark.asyncio
async def test_has_components(entity_with_components):
    """Test checking if an entity has specific components."""
    assert await entity_with_components.has_components(Position, Velocity)
    assert await entity_with_components.has_components(Identity)
    assert not await entity_with_components.has_components(Component)  # Should be False


@pytest.mark.asyncio
async def test_remove_component(entity_with_components):
    """Test removing a component from an entity."""
    await entity_with_components.remove_component(Velocity)
    assert await entity_with_components.get_component(Velocity) is None


@pytest.mark.asyncio
async def test_get_component_with_subclasses(entity):
    """Test retrieving components including subclasses."""

    class Animal(Component):
        species: str

    class Dog(Animal):
        breed: str

    dog = Dog(species="canine", breed="retriever")
    await entity.add_component(dog)

    # Act & Assert
    assert await entity.get_component(Animal, include_subclasses=True) == dog
