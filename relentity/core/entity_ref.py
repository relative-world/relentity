from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .entities import Entity


class EntityRef:
    """Safe entity reference that avoids dangling references."""

    def __init__(self, entity: "Entity"):
        self.entity_id = entity.id
        self.registry = entity.registry

    async def resolve(self) -> Optional["Entity"]:
        """Resolve to the entity if it still exists, None otherwise."""
        return self.registry.get_entity_by_id(self.entity_id)

    async def is_valid(self) -> bool:
        """Check if the referenced entity still exists."""
        return await self.resolve() is not None
