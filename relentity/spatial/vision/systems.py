from relentity.spatial import Position, Velocity
from relentity.spatial.events import EntitySeenEvent, ENTITY_SEEN_EVENT_TYPE
from relentity.spatial.vision.components import Vision, Visible
from relentity.spatial.systems import SpatialSystem


class VisionSystem(SpatialSystem):
    """
    System for detecting entities within the vision range of other entities.

    Methods:
        update: Detects entities within the vision range and emits ENTITY_SEEN_EVENT_TYPE events.
    """

    async def update(self, delta_time: float = 0) -> None:
        """
        Detects entities within the vision range of entities with Vision and Position components.
        Emits an ENTITY_SEEN_EVENT_TYPE event for each detected entity.
        """
        async for entity_ref in self.registry.entities_with_components(Vision, Position):
            entity = await entity_ref.resolve()
            vision = await entity.get_component(Vision)
            position = await entity.get_component(Position)
            async for other_entity_ref in self.registry.entities_within_distance(position, vision.max_range, Visible):
                if other_entity_ref.entity_id != entity.id:
                    other_entity = await other_entity_ref.resolve()
                    other_position = await other_entity.get_component(Position)
                    other_velocity = await other_entity.get_component(Velocity)
                    event = EntitySeenEvent(
                        entity_ref=other_entity_ref, position=other_position, velocity=other_velocity
                    )
                    await entity.event_bus.emit(ENTITY_SEEN_EVENT_TYPE, event)
