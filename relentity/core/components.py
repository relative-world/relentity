from typing import TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class Component(BaseModel):
    """
    Base class for all components in the system.
    Inherits from Pydantic's BaseModel to provide data validation and serialization.
    """
    pass

class Identity(Component):
    """
    Component that represents the identity of an entity.

    Attributes:
        name (str): The name of the entity.
        description (str): A description of the entity.
    """
    name: str
    description: str
