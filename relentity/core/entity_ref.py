import uuid
from typing import Optional, TYPE_CHECKING, Annotated, Any

from pydantic import BaseModel, PrivateAttr


if TYPE_CHECKING:
    from .entities import Entity


class EntityRef(BaseModel):
    """Safe entity reference that avoids dangling references."""

    entity_id: uuid.UUID
    registry: Annotated[Any, PrivateAttr()]

    async def resolve(self) -> Optional["Entity"]:
        """Resolve to the entity if it still exists, None otherwise."""
        return await self.registry.get_entity_by_id(self.entity_id)

    async def is_valid(self) -> bool:
        """Check if the referenced entity still exists."""
        return await self.resolve() is not None
