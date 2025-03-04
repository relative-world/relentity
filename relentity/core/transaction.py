class Transaction:
    def __init__(self, registry):
        self.registry = registry
        self.changes = []

    async def commit(self):
        for entity_id, component, operation in self.changes:
            if operation == "add":
                await self.registry.add_component(entity_id, component)
