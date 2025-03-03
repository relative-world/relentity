from relentity.core import EntityRef
from .components import Velocity, Position, Area

ENTITY_SEEN_EVENT_TYPE = "entity_seen"
POSITION_UPDATED_EVENT_TYPE = "position_updated"
SOUND_HEARD_EVENT_TYPE = "sound_heard"
SOUND_CREATED_EVENT_TYPE = "sound_created"
AREA_ENTERED_EVENT_TYPE = "area.entered"
AREA_EXITED_EVENT_TYPE = "area.exited"


class EntitySeenEvent:
    """
    Event representing an entity being seen.

    Attributes:
        entity (Entity): The entity that was seen.
        position (Position): The position of the seen entity.
        velocity (Velocity): The velocity of the seen entity.
    """

    def __init__(self, entity_ref: EntityRef, position: Position, velocity: Velocity):
        """
        Initializes an EntitySeenEvent.

        Args:
            entity (Entity): The entity that was seen.
            position (Position): The position of the seen entity.
            velocity (Velocity): The velocity of the seen entity.
        """
        self.entity_ref = entity_ref
        self.position = position
        self.velocity = velocity


class SoundEvent:
    """
    Event representing a sound.

    Attributes:
        entity (Entity): The entity that created the sound.
        sound_type (str): The type of the sound.
        sound (str): The sound itself.
    """

    def __init__(self, entity_ref: EntityRef, sound_type: str, sound: str):
        """
        Initializes a SoundEvent.

        Args:
            entity (Entity): The entity that created the sound.
            sound_type (str): The type of the sound.
            sound (str): The sound itself.
        """
        self.entity_ref = entity_ref
        self.sound_type = sound_type
        self.sound = sound


class AreaEvent:
    """
    Event representing an entity entering or exiting an area.

    Attributes:
        entity (Entity): The entity that entered or exited the area.
        area (str): The area that was entered or exited.
    """

    def __init__(self, entity_ref: EntityRef, area_entity_ref: Area):
        """
        Initializes an AreaEvent.

        Args:
            entity (Entity): The entity that entered or exited the area.
            area (str): The area that was entered or exited.
        """
        self.entity_ref = entity_ref
        self.area_entity_ref = area_entity_ref
