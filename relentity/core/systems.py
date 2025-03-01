from .registry import Registry


class System:
    def __init__(self, registry: Registry):
        self.registry = registry

    async def update(self):
        raise NotImplementedError
