from relentity.core import Component


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
