import pytest

from relentity.core.components import Component
from relentity.core.entities import Entity


# Define test components
class _Position(Component):
    x: float = 0
    y: float = 0


def get_test_position():
    return _Position(x=10, y=20)


class _Velocity(Component):
    vx: float = 0
    vy: float = 0


@pytest.mark.asyncio
async def test_entity_metaclass_with_component_instances(registry):
    """Test EntityMeta with component instances."""
    # Arrange
    EntityWithComponents = Entity[_Position(x=5, y=10), _Velocity(vx=1, vy=2)]

    # Act
    entity = EntityWithComponents(registry)

    # Assert
    assert (await entity.get_component(_Position)).x == 5
    assert (await entity.get_component(_Velocity)).vx == 1


@pytest.mark.asyncio
async def test_entity_metaclass_with_callable(registry):
    """Test EntityMeta with callable function."""
    # Arrange
    EntityWithPosition = Entity[get_test_position]

    # Act
    entity = EntityWithPosition(registry)

    # Assert
    position = await entity.get_component(_Position)
    assert position.x == 10
    assert position.y == 20


@pytest.mark.asyncio
async def test_entity_metaclass_with_mixed_components(registry):
    """Test EntityMeta with both instances and callables."""
    # Arrange
    EntityMixed = Entity[get_test_position, _Velocity(vx=3, vy=4)]

    # Act
    entity = EntityMixed(registry)

    # Assert
    position = await entity.get_component(_Position)
    velocity = await entity.get_component(_Velocity)
    assert position.x == 10
    assert velocity.vx == 3
