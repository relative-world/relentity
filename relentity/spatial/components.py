from relentity.core import Component


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
