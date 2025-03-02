from typing import Any


# Entity Lifecyle events
ENTITY_CREATED_EVENT = "entity.created"
ENTITY_DESTROYED_EVENT = "entity.destroyed"
ENTITY_COMPONENT_ADDED_EVENT = "entity.component_added"
ENTITY_COMPONENT_REMOVED_EVENT = "entity.component_removed"
ENTITY_COMPONENT_UPDATED_EVENT = "entity.component_updated"
ENTITY_COMPONENT_REPLACED_EVENT = "entity.component_replaced"


class Event:
    def __init__(self, name: str, data: Any = None):
        """
        Initializes an Event with a name and optional data.

        Args:
            name (str): The name of the event.
            data (Any, optional): The data associated with the event. Defaults to None.
        """
        self.name: str = name
        self.data: Any = data
