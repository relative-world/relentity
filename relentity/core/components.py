from typing import TypeVar

from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class Component(BaseModel): ...


class Identity(Component):
    name: str
    description: str
