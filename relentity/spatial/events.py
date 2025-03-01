from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from relentity.core import Entity

    from .components import Velocity, Position

ENTITY_SEEN_EVENT_TYPE = "entity_seen"
POSITION_UPDATED_EVENT_TYPE = "position_updated"
SOUND_HEARD_EVENT_TYPE = "sound_heard"
SOUND_CREATED_EVENT_TYPE = "sound_created"


class EntitySeenEvent:
    def __init__(self, entity: 'Entity', position: 'Position', velocity: 'Velocity'):
        self.entity = entity
        self.position = position
        self.velocity = velocity


class SoundEvent:
    def __init__(self, entity, sound_type: str, sound: str):
        self.entity = entity
        self.sound_type = sound_type
        self.sound = sound
