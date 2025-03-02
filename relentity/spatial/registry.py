from math import sqrt
from typing import Type

from relentity.core import Registry, Component
from .components import Position


class SpatialRegistry(Registry):
    """
    A specialized registry for spatial entities, providing additional methods for spatial queries.
    """

    async def entities_within_distance(self, centroid: Position, distance: float, *component_types: Type[Component]):
        """
        Yields entities within a specified distance from a given position that have the specified components.

        Args:
            centroid (Position): The central position to measure distance from.
            distance (float): The maximum distance from the centroid.
            component_types (Type[Component]): The types of components the entities must have.

        Yields:
            Entity: An entity within the specified distance that has the specified components.
        """
        for entity in self.entities:
            position = await entity.get_component(Position)
            if position:
                dist = sqrt((position.x - centroid.x) ** 2 + (position.y - centroid.y) ** 2)
                if dist <= distance:
                    if all([await entity.get_component(component_type) for component_type in component_types]):
                        yield entity