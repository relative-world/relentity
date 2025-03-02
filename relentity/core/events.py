from typing import Any


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
