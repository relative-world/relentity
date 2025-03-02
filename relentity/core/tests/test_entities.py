import pytest

from relentity.core import Entity
from relentity.core.components import Component, Identity
from relentity.spatial import Position, Velocity


# Use fixtures from conftest.py for registry


@pytest.mark.asyncio
async def test_add_component(registry):
    """Test adding a component to an entity."""

    entity = Entity(registry)
    position = Position(x=10, y=20)

    await entity.add_component(position)
    assert await entity.get_component(Position) == position
    assert position in entity.components.values()


@pytest.mark.asyncio
async def test_get_component(registry):
    """Test retrieving a component from an entity."""
    entity = Entity[
        Position(x=0, y=0),
        Velocity(vx=1, vy=0),
        Identity(name="Test Entity", description="An entity for testing"),
    ](registry)

    assert (await entity.get_component(Position)).x == 0
    assert (await entity.get_component(Velocity)).vx == 1
    assert (await entity.get_component(Identity)).name == "Test Entity"


@pytest.mark.asyncio
async def test_has_components(registry):
    """Test checking if an entity has specific components."""
    entity = Entity[
        Position(x=0, y=0),
        Velocity(vx=1, vy=0),
        Identity(name="Test Entity", description="An entity for testing"),
    ](registry)

    assert await entity.has_components(Position, Velocity)
    assert await entity.has_components(Identity)
    assert not await entity.has_components(Component)  # Should be False


@pytest.mark.asyncio
async def test_remove_component(registry):
    """Test removing a component from an entity."""
    entity = Entity[
        Position(x=0, y=0),
        Velocity(vx=1, vy=0),
        Identity(name="Test Entity", description="An entity for testing"),
    ](registry)

    await entity.remove_component(Velocity)
    assert await entity.get_component(Velocity) is None


@pytest.mark.asyncio
async def test_get_component_with_subclasses(registry):
    """Test retrieving components including subclasses."""

    entity = Entity(registry)

    class Animal(Component):
        species: str

    class Dog(Animal):
        breed: str

    dog = Dog(species="canine", breed="retriever")
    await entity.add_component(dog)

    # Act & Assert
    assert await entity.get_component(Animal, include_subclasses=True) == dog
