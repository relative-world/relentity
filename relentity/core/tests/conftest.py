import pytest

from relentity.core.components import Identity
from relentity.core.entities import Entity
from relentity.core.event_bus import EventBus
from relentity.core.registry import Registry
from relentity.spatial import Velocity, Position


@pytest.fixture
def registry():
    """Provides a clean Registry instance for tests."""
    return Registry()


@pytest.fixture
def event_bus():
    """Provides a clean EventBus instance for tests."""
    return EventBus()


@pytest.fixture
def entity(registry):
    """Provides a basic Entity instance attached to the registry."""
    return Entity(registry)


@pytest.fixture
def entity_with_components(registry):
    """Provides an Entity with predefined components."""
    e = Entity[
        Position(x=0, y=0),
        Velocity(vx=1, vy=0),
        Identity(name="Test Entity", description="An entity for testing"),
    ](registry)
    return e
