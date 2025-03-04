from enum import Enum

from relentity.core.components import Component


class ShapeType(Enum):
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"


class ShapeBody(Component):
    shape_type: ShapeType
    # For circles
    radius: int = 10
    # For rectangles
    width: int = 20
    height: int = 20
