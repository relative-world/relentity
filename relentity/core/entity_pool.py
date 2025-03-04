from relentity.core import Entity


class EntityPool:
    def __init__(self, size=1000):
        self.free_entities = []
        self.size = size

    def get(self, registry):
        if not self.free_entities:
            # Create new entities
            return Entity(registry)

        return self.free_entities.pop()

    def recycle(self, entity):
        if len(self.free_entities) < self.size:
            # Reset entity state
            entity.components.clear()
            self.free_entities.append(entity)
