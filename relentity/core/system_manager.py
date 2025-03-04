from typing import List

from relentity.core import System


class SystemManager:
    def __init__(self):
        self.systems: List[System] = []

    def add_system(self, system: System) -> None:
        self.systems.append(system)
        self.systems.sort(key=lambda s: s.priority)

    async def update(self, delta_time: float = 0) -> None:
        for system in self.systems:
            await system.process(delta_time)
