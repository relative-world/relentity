from typing import Annotated

from pydantic import PrivateAttr

from relentity.core import Component
from relentity.spatial.events import SoundEvent


class Audible(Component):
    """
    Component representing the audibility of an entity.

    Attributes:
        volume (float): The volume level of the entity.
        _output_queue (list[SoundEvent]): A private queue of sound events to be emitted by the entity.
    """

    volume: float = 50.0
    _output_queue: Annotated[list["SoundEvent"], PrivateAttr()] = []

    def queue_sound(self, sound_event: "SoundEvent"):
        """
        Queues a sound event to be emitted by the entity.

        Args:
            sound_event (SoundEvent): The sound event to queue.
        """
        self._output_queue.append(sound_event)

    def retrieve_queue(self, clear=False):
        """
        Retrieves the queue of sound events.

        Args:
            clear (bool, optional): Whether to clear the queue after retrieval. Defaults to False.

        Returns:
            list[SoundEvent]: The list of sound events in the queue.
        """
        output = self._output_queue
        if clear:
            self._output_queue = []
        return output


class Hearing(Component):
    """
    Component representing the hearing capability of an entity.

    Attributes:
        volume (float): The volume level of the entity's hearing.
        _output_queue (list[SoundEvent]): A private queue of sound events heard by the entity.
    """

    volume: float = 50.0
    _output_queue: Annotated[list[SoundEvent], PrivateAttr()] = []

    def queue_sound(self, sound_event: SoundEvent):
        """
        Queues a sound event that the entity has heard.

        Args:
            sound_event (SoundEvent): The sound event to queue.
        """
        self._output_queue.append(sound_event)

    def retrieve_queue(self, clear=False):
        """
        Retrieves the queue of sound events heard by the entity.

        Args:
            clear (bool, optional): Whether to clear the queue after retrieval. Defaults to False.

        Returns:
            list[SoundEvent]: The list of sound events in the queue.
        """
        output = self._output_queue
        if clear:
            self._output_queue = []
        return output
