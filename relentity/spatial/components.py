from typing import Annotated, TYPE_CHECKING

from pydantic import PrivateAttr, model_validator

from relentity.core import Component
from .utils import is_simple_polygon, point_in_polygon
from ..core.entity_ref import EntityRef

if TYPE_CHECKING:
    pass


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
