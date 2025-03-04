import uuid
from typing import Type, Set

from relentity.core import Component


class Archetype:
    def __init__(self, component_types: Set[Type[Component]]):
        self.component_types = frozenset(component_types)
        self.entities: Set[uuid.UUID] = set()
