from math import sqrt
from typing import Type

from relentity.core import Registry, Component
from .components import Position


class SpatialRegistry(Registry):

    async def entities_within_distance(self, centroid: Position, distance: float, *component_types: Type[Component]):
        for entity in self.entities:
            position = await entity.get_component(Position)
            if position:
                dist = sqrt((position.x - centroid.x) ** 2 + (position.y - centroid.y) ** 2)
                if dist <= distance:
                    if all([await entity.get_component(component_type) for component_type in component_types]):
                        yield entity
