from typing import Annotated, TYPE_CHECKING

from pydantic import PrivateAttr, model_validator

from relentity.core import Component
from .utils import is_simple_polygon, point_in_polygon
from ..core.entity_ref import EntityRef

if TYPE_CHECKING:
    from .events import SoundEvent


class Position(Component):
    """
    Component representing the position of an entity in 2D space.

    Attributes:
        x (float): The x-coordinate of the entity.
        y (float): The y-coordinate of the entity.
    """

    x: float
    y: float


class Velocity(Component):
    """
    Component representing the velocity of an entity in 2D space.

    Attributes:
        vx (float): The velocity of the entity along the x-axis.
        vy (float): The velocity of the entity along the y-axis.
    """

    vx: float
    vy: float


class Vision(Component):
    """
    Component representing the vision capability of an entity.

    Attributes:
        max_range (float): The maximum range of vision for the entity.
    """

    max_range: float


class Visible(Component):
    """
    Component representing the visibility of an entity.

    Attributes:
        description (str): A description of the visible entity.
    """

    description: str = "A visible entity"


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
    _output_queue: Annotated[list["SoundEvent"], PrivateAttr()] = []

    def queue_sound(self, sound_event: "SoundEvent"):
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


class Area(Component):
    """ """

    center_point: tuple[float, float] = (0.0, 0.0)
    geometry: list[tuple[float, float]]
    _entities: Annotated[set[EntityRef], PrivateAttr()] = set()

    @model_validator(mode="after")
    def validate_geometry(cls, self):
        if not is_simple_polygon(self.geometry):
            raise ValueError("The geometry is not a simple polygon.")
        return self

    def point_within_bounds(self, x, y):
        """
        Check if a point is within the bounds of the location.

        Args:
            point (tuple[float, float]): The point to check.

        Returns:
            bool: True if the point is within the bounds, False otherwise.
        """
        point_in_polygon(x, y, self.geometry)


class Located(Component):
    """
    Component representing the location of an entity within an area.

    Attributes:
        area (Area): The area the entity is located in.
    """

    area_entity_ref: EntityRef
