ENTITY_SEEN_EVENT_TYPE = "entity_seen"
POSITION_UPDATED_EVENT_TYPE = "position_updated"

class EntitySeenEvent:
    def __init__(self, entity, position):
        self.entity = entity
        self.position = position
