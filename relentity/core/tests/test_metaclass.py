import pytest

from relentity.core.components import Component
from relentity.core.entities import Entity


# Define test components
class TestPosition(Component):
    x: float = 0
    y: float = 0


def get_test_position():
    return TestPosition(x=10, y=20)


class TestVelocity(Component):
    vx: float = 0
    vy: float = 0


@pytest.mark.asyncio
async def test_entity_metaclass_with_component_instances(registry):
    """Test EntityMeta with component instances."""
    # Arrange
    EntityWithComponents = Entity[TestPosition(x=5, y=10), TestVelocity(vx=1, vy=2)]

    # Act
    entity = EntityWithComponents(registry)

    # Assert
    assert (await entity.get_component(TestPosition)).x == 5
    assert (await entity.get_component(TestVelocity)).vx == 1


@pytest.mark.asyncio
async def test_entity_metaclass_with_callable(registry):
    """Test EntityMeta with callable function."""
    # Arrange
    EntityWithPosition = Entity[get_test_position]

    # Act
    entity = EntityWithPosition(registry)

    # Assert
    position = await entity.get_component(TestPosition)
    assert position.x == 10
    assert position.y == 20


@pytest.mark.asyncio
async def test_entity_metaclass_with_mixed_components(registry):
    """Test EntityMeta with both instances and callables."""
    # Arrange
    EntityMixed = Entity[get_test_position, TestVelocity(vx=3, vy=4)]

    # Act
    entity = EntityMixed(registry)

    # Assert
    position = await entity.get_component(TestPosition)
    velocity = await entity.get_component(TestVelocity)
    assert position.x == 10
    assert velocity.vx == 3
