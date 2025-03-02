from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from relentity.core import Entity
    from .components import Velocity, Position

ENTITY_SEEN_EVENT_TYPE = "entity_seen"
"""
Constant representing the event type for an entity being seen.
"""

POSITION_UPDATED_EVENT_TYPE = "position_updated"
"""
Constant representing the event type for an entity's position being updated.
"""

SOUND_HEARD_EVENT_TYPE = "sound_heard"
"""
Constant representing the event type for a sound being heard.
"""

SOUND_CREATED_EVENT_TYPE = "sound_created"
"""
Constant representing the event type for a sound being created.
"""


class EntitySeenEvent:
    """
    Event representing an entity being seen.

    Attributes:
        entity (Entity): The entity that was seen.
        position (Position): The position of the seen entity.
        velocity (Velocity): The velocity of the seen entity.
    """

    def __init__(self, entity: "Entity", position: "Position", velocity: "Velocity"):
        """
        Initializes an EntitySeenEvent.

        Args:
            entity (Entity): The entity that was seen.
            position (Position): The position of the seen entity.
            velocity (Velocity): The velocity of the seen entity.
        """
        self.entity = entity
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

    def __init__(self, entity: "Entity", sound_type: str, sound: str):
        """
        Initializes a SoundEvent.

        Args:
            entity (Entity): The entity that created the sound.
            sound_type (str): The type of the sound.
            sound (str): The sound itself.
        """
        self.entity = entity
        self.sound_type = sound_type
        self.sound = sound