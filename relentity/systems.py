from relentity.registry import Registry


class System:
    def __init__(self, registry: Registry):
        self.registry = registry

    def update(self):
        raise NotImplementedError
