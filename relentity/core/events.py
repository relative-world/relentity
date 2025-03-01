from typing import Any

class Event:
    def __init__(self, name: str, data: Any = None):
        self.name = name
        self.data = data
