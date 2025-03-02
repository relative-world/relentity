import pytest
from relentity.ai.utils import pretty_name_entity, pretty_print_event
from relentity.core import Identity
from relentity.spatial import (
    Visible,
    Velocity,
    Position,
    ENTITY_SEEN_EVENT_TYPE,
    POSITION_UPDATED_EVENT_TYPE,
    SOUND_HEARD_EVENT_TYPE,
    SOUND_CREATED_EVENT_TYPE,
    SpatialRegistry,
)
from relentity.tasks.events import TASK_PROGRESS_EVENT_TYPE, TASK_COMPLETE_EVENT_TYPE, TASK_ABANDONED_EVENT_TYPE
from relentity.core import Entity, Event
from relentity.spatial.events import EntitySeenEvent, SoundEvent
from relentity.tasks.components import Task


@pytest.fixture
def registry():
    return SpatialRegistry()


@pytest.mark.asyncio
async def test_pretty_name_entity(registry):
    entity = Entity[Identity(name="Test Entity", description="A test entity")](registry)
    result = await pretty_name_entity(entity)
    assert result == "Test Entity"

    entity = Entity(registry)
    result = await pretty_name_entity(entity)
    assert result == repr(entity)


@pytest.mark.asyncio
async def test_pretty_print_event_position_updated(registry):
    data = Position(x=10.0, y=20.0)
    result = await pretty_print_event(POSITION_UPDATED_EVENT_TYPE, data)
    assert result == "Position updated to (10.0, 20.0)"


@pytest.mark.asyncio
async def test_pretty_print_event_entity_seen(registry):
    entity = Entity[
        Identity(name="Test Entity", description="A test entity"),
        Visible(description="A visible entity"),
        Velocity(vx=5.0, vy=5.0),
        Position(x=10.0, y=20.0),
    ](registry)
    data = EntitySeenEvent(
        entity=entity, position=await entity.get_component(Position), velocity=await entity.get_component(Velocity)
    )

    result = await pretty_print_event(ENTITY_SEEN_EVENT_TYPE, data)
    assert result == "You see Test Entity is at (10.0, 20.0) - (A visible entity) moving at velocity (5.0, 5.0)"

    result = await pretty_print_event(ENTITY_SEEN_EVENT_TYPE, data, past_tense=True)
    assert result == "You last saw Test Entity at (10.0, 20.0) - (A visible entity) moving at velocity (5.0, 5.0)"


@pytest.mark.asyncio
async def test_pretty_print_event_sound_heard(registry):
    entity = Entity[Identity(name="Sound Source", description="A sound source")](registry)
    data = SoundEvent(entity=entity, sound_type="noise", sound="A loud noise")

    result = await pretty_print_event(SOUND_HEARD_EVENT_TYPE, data)
    assert result == "Sound heard: source=Sound Source, sound=A loud noise, type=noise"


@pytest.mark.asyncio
async def test_pretty_print_event_sound_created(registry):
    entity = Entity(registry)
    data = SoundEvent(entity=entity, sound="Hello, world!", sound_type="speech")
    result = await pretty_print_event(SOUND_CREATED_EVENT_TYPE, data)
    assert result == "You said: Hello, world!"


@pytest.mark.asyncio
async def test_pretty_print_event_task_progress():
    data = Task(task="Test Task", remaining_cycles=50)

    result = await pretty_print_event(TASK_PROGRESS_EVENT_TYPE, data)
    assert result == "Task progress: Test Task - 50 cycles remaining"


@pytest.mark.asyncio
async def test_pretty_print_event_task_complete():
    data = Task(task="Test Task", remaining_cycles=0)

    result = await pretty_print_event(TASK_COMPLETE_EVENT_TYPE, data)
    assert result == "Task complete: Test Task"


@pytest.mark.asyncio
async def test_pretty_print_event_task_abandoned():
    data = Task(task="Test Task", remaining_cycles=50)

    result = await pretty_print_event(TASK_ABANDONED_EVENT_TYPE, data)
    assert result == "Task abandoned: Test Task - 50 cycles remained"
