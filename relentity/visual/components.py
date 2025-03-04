from enum import Enum
from typing import Tuple

from relentity.core.components import Component


class ShapeType(Enum):
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"


class RenderableShape(Component):
    shape_type: ShapeType = ShapeType.CIRCLE
    radius: int = 10  # For circles
    width: int = 20  # For rectangles
    height: int = 20  # For rectangles


class RenderableColor(Component):
    r: int = 255
    g: int = 255
    b: int = 255
    alpha: int = 255

    @property
    def rgba(self) -> Tuple[int, int, int, int]:
        return (self.r, self.g, self.b, self.alpha)


class RenderLayer(Component):
    layer: int = 0  # Higher layers render on top


class SpeechBubble(Component):
    text: str
    duration: float  # Duration in seconds
    start_time: float  # Time when the speech bubble was created
