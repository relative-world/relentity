import pytest
from unittest.mock import AsyncMock

from relentity.core.entities import Entity
from relentity.spatial.registry import SpatialRegistry
from relentity.spatial.components import Position
from relentity.spatial.events import SoundEvent, SOUND_HEARD_EVENT_TYPE, SOUND_CREATED_EVENT_TYPE
from relentity.spatial.sensory.components import Hearing, Audible
from relentity.spatial.sensory.systems import AudioSystem


@pytest.fixture
def registry():
    return SpatialRegistry()


@pytest.fixture
def audio_system(registry):
    return AudioSystem(registry)


@pytest.mark.asyncio
async def test_hearing_entity_processes_sound_queue(registry, audio_system):
    # Create entity with hearing
    hearing_entity = Entity[Position(x=0, y=0), Hearing()](registry)
    # Mock the emit method to track calls
    hearing_entity.event_bus.emit = AsyncMock()

    # Add a sound event to the hearing queue
    hearing = await hearing_entity.get_component(Hearing)
    sound_event = SoundEvent(hearing_entity, "test", "Hello!")
    hearing.queue_sound(sound_event)

    # Update the system
    await audio_system.update()

    # Verify that SOUND_HEARD_EVENT_TYPE was emitted with the sound event
    hearing_entity.event_bus.emit.assert_called_once_with(SOUND_HEARD_EVENT_TYPE, sound_event)

    # Queue should be cleared
    assert not hearing.retrieve_queue()


@pytest.mark.asyncio
async def test_sound_propagation_within_range(registry, audio_system):
    # Create sound source entity
    source_entity = Entity[Position(x=0, y=0), Audible(volume=50)](registry)

    # Create listener entity within range
    listener_entity = Entity[Position(x=30, y=40), Hearing()](registry)  # Distance = 50

    # Mock event bus emissions
    source_entity.event_bus.emit = AsyncMock()

    # Create sound event
    audible = await source_entity.get_component(Audible)
    sound_event = SoundEvent(source_entity, "voice", "Hello!")
    audible.queue_sound(sound_event)

    # Update the system
    await audio_system.update()

    # Verify that SOUND_CREATED_EVENT_TYPE was emitted
    source_entity.event_bus.emit.assert_called_with(SOUND_CREATED_EVENT_TYPE, sound_event)

    # Verify the listener received the sound
    hearing = await listener_entity.get_component(Hearing)
    received_sounds = hearing.retrieve_queue()
    assert len(received_sounds) == 1
    assert received_sounds[0] == sound_event


@pytest.mark.asyncio
async def test_sound_propagation_outside_range(registry, audio_system):
    # Create sound source with volume 30
    source_entity = Entity[Position(x=0, y=0), Audible(volume=30)](registry)

    # Create listener entity outside range
    listener_entity = Entity[Position(x=40, y=0), Hearing()](registry)  # Distance = 40 > 30

    # Create sound event
    audible = await source_entity.get_component(Audible)
    sound_event = SoundEvent(source_entity, "voice", "Hello!")
    audible.queue_sound(sound_event)

    # Update the system
    await audio_system.update()

    # Verify the listener did NOT receive the sound (out of range)
    hearing = await listener_entity.get_component(Hearing)
    assert not hearing.retrieve_queue()


@pytest.mark.asyncio
async def test_multiple_listeners(registry, audio_system):
    # Create sound source
    source_entity = Entity[Position(x=0, y=0), Audible(volume=100)](registry)

    # Create multiple listeners at different distances
    listener1 = Entity[Position(x=50, y=0), Hearing()](registry)  # Distance = 50
    listener2 = Entity[Position(x=0, y=80), Hearing()](registry)  # Distance = 80
    listener3 = Entity[Position(x=120, y=0), Hearing()](registry)  # Distance = 120 (out of range)

    # Create sound event
    audible = await source_entity.get_component(Audible)
    sound_event = SoundEvent(source_entity, "voice", "Hello everyone!")
    audible.queue_sound(sound_event)

    # Update the system
    await audio_system.update()

    # Verify appropriate listeners received the sound
    hearing1 = await listener1.get_component(Hearing)
    hearing2 = await listener2.get_component(Hearing)
    hearing3 = await listener3.get_component(Hearing)

    assert len(hearing1.retrieve_queue()) == 1
    assert len(hearing2.retrieve_queue()) == 1
    assert len(hearing3.retrieve_queue()) == 0
