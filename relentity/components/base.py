from typing import TypeVar, ClassVar

from pydantic import BaseModel

class Component(BaseModel):
    T: ClassVar = TypeVar('T', bound=BaseModel)
