from typing import Annotated

from pydantic import PrivateAttr

from relentity.core import Component
from .events import SoundEvent


class Position(Component):
    x: float
    y: float


class Velocity(Component):
    vx: float
    vy: float


class Acceleration(Component):
    vx: float
    vy: float


class Vision(Component):
    max_range: float


class Visible(Component):
    description: str


class Audible(Component):
    volume: float = 50.
    _output_queue: Annotated[list[SoundEvent], PrivateAttr()] = []

    def queue_sound(self, sound_event: SoundEvent):
        self._output_queue.append(sound_event)

    def retrieve_queue(self, clear=False):
        output = self._output_queue
        if clear:
            self._output_queue = []
        return output


class Hearing(Component):
    volume: float = 50.
    _output_queue: Annotated[list[SoundEvent], PrivateAttr()] = []

    def queue_sound(self, sound_event: SoundEvent):
        self._output_queue.append(sound_event)

    def retrieve_queue(self, clear=False):
        output = self._output_queue
        if clear:
            self._output_queue = []
        return output

