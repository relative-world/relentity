from .components import Position, Velocity, Area, Located
from .events import (
    POSITION_UPDATED_EVENT_TYPE,
    AreaEvent,
)
from .events import AREA_ENTERED_EVENT_TYPE, AREA_EXITED_EVENT_TYPE
from .registry import SpatialRegistry
from ..core import Entity, System
from ..core.entity_ref import EntityRef
from ..core.exceptions import UnknownComponentError


class SpatialSystem(System):
    """
    Base class for spatial systems, providing common functionality for systems that operate on spatial entities.

    Args:
        registry (SpatialRegistry): The registry to be used by the system.
    """

    def __init__(self, registry: SpatialRegistry):
        """
        Initializes the SpatialSystem with a registry.

        Args:
            registry (SpatialRegistry): The registry to be used by the system.
        """
        super().__init__(registry)
        self.registry = registry


class MovementSystem(SpatialSystem):
    _entity_cache = {}
    _cache_ttl = 10
    _cache_counter = {}

    def __init__(self, registry: SpatialRegistry, max_speed: float = 10):
        """
        Initializes the MovementSystem with a registry and a maximum speed for entities.

        Args:
            registry (SpatialRegistry): The registry to be used by the system.
            max_speed (float, optional): The maximum speed for entities. Defaults to 10.
        """
        super().__init__(registry)
        self.max_speed = max_speed
        # Pre-calculate constants
        self._max_speed_squared = max_speed * max_speed

    async def update(self, delta_time: float = 0) -> None:
        # Process cache expiration only every few frames to reduce overhead
        if hasattr(self, "_frame_counter"):
            self._frame_counter = (self._frame_counter + 1) % 5
            if self._frame_counter == 0:
                self._process_cache_expiration()
        else:
            self._frame_counter = 0

        # Fast path for zero delta time
        if delta_time == 0:
            delta_time = 0.016  # Default to ~60fps if not specified

        # Reuse list to avoid allocation
        if not hasattr(self, "_entities_data"):
            self._entities_data = []
        else:
            self._entities_data.clear()

        # Collect entities using cache
        async for entity_ref in self.registry.entities_with_components(Position, Velocity):
            entity_id = entity_ref.entity_id

            if entity_id in self._entity_cache:
                entity, position, velocity = self._entity_cache[entity_id]
                self._cache_counter[entity_id] = 0
            else:
                entity = await entity_ref.resolve()
                position = await entity.get_component(Position)
                velocity = await entity.get_component(Velocity)
                self._entity_cache[entity_id] = (entity, position, velocity)
                self._cache_counter[entity_id] = 0

            self._entities_data.append((entity, position, velocity))

        # Process all entities efficiently
        for entity, position, velocity in self._entities_data:
            # Skip update for stationary objects
            if velocity.vx == 0 and velocity.vy == 0:
                continue

            # Use squared comparison
            speed_squared = velocity.vx * velocity.vx + velocity.vy * velocity.vy

            if speed_squared > self._max_speed_squared:
                # Compute scale without sqrt when possible using fast approximation
                inv_speed = self._fast_inverse_sqrt(speed_squared)
                scale = self.max_speed * inv_speed
                velocity.vx *= scale
                velocity.vy *= scale

            # Apply movement with delta time
            position.x += velocity.vx * delta_time
            position.y += velocity.vy * delta_time

        # Emit events only for moved entities
        for entity, position, velocity in self._entities_data:
            if velocity.vx != 0 or velocity.vy != 0:
                await entity.event_bus.emit(POSITION_UPDATED_EVENT_TYPE, position)

    def _process_cache_expiration(self):
        for entity_id in list(self._cache_counter.keys()):
            self._cache_counter[entity_id] += 1
            if self._cache_counter[entity_id] > self._cache_ttl:
                self._entity_cache.pop(entity_id, None)
                self._cache_counter.pop(entity_id, None)

    @staticmethod
    def _fast_inverse_sqrt(number):
        """Fast inverse square root approximation (or fallback to regular method)"""
        return 1.0 / (number**0.5)


class LocationSystem(SpatialSystem):
    async def update(self, delta_time: float = 0) -> None:
        async for area_entity_ref in self.registry.entities_with_components(Area):
            area_entity: Entity = await area_entity_ref.resolve()
            area: Area = await area_entity.get_component(Area)

            existing_entity_refs: set[EntityRef] = area._entities
            _updated_entity_refs: set[EntityRef] = set()
            async for entity_ref in self.registry.entities_within_area(area):
                _updated_entity_refs.add(entity_ref)
                if entity_ref not in existing_entity_refs:
                    entity = await entity_ref.resolve()
                    try:
                        await entity.remove_component(Located)
                    except UnknownComponentError:
                        pass

                    await entity.add_component(Located(area_entity_ref=area_entity_ref))
                    event = AreaEvent(entity_ref=entity_ref, area_entity_ref=area_entity_ref)
                    await entity.event_bus.emit(AREA_ENTERED_EVENT_TYPE, event)
                    await area_entity.event_bus.emit(AREA_ENTERED_EVENT_TYPE, event)

            old_refs = existing_entity_refs - _updated_entity_refs
            for entity_ref in old_refs:
                entity = await entity_ref.resolve()
                event = AreaEvent(entity_ref=entity_ref, area_entity_ref=area_entity_ref)
                await self.registry.remove_component_from_entity(entity.id, Located)
                await entity.event_bus.emit(AREA_EXITED_EVENT_TYPE, event)
                await area_entity.event_bus.emit(AREA_EXITED_EVENT_TYPE, event)

            area._entities = _updated_entity_refs
