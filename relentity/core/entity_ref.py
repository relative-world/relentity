import uuid
from typing import Optional, TYPE_CHECKING, Annotated, Any

from pydantic import BaseModel, PrivateAttr


if TYPE_CHECKING:
    from .entities import Entity


class EntityRef(BaseModel):
    """Safe entity reference that avoids dangling references."""

    entity_id: uuid.UUID
    _registry: Annotated[Any, PrivateAttr()] = None

    def __init__(self, *args, _registry=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._registry = _registry

    async def resolve(self) -> Optional["Entity"]:
        """Resolve to the entity if it still exists, None otherwise."""
        return await self._registry.get_entity_by_id(self.entity_id)

    async def is_valid(self) -> bool:
        """Check if the referenced entity still exists."""
        return await self.resolve() is not None

    def __hash__(self) -> int:
        return hash(self.entity_id)
