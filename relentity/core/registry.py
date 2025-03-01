class Registry:
    def __init__(self):
        self.entities = set()
        self.component_to_entities = {}

    def register_entity(self, entity):
        self.entities.add(entity)
        for component_type in entity.components:
            if component_type not in self.component_to_entities:
                self.component_to_entities[component_type] = set()
            self.component_to_entities[component_type].add(entity)

    async def entities_with_components(self, *component_types, include_subclasses=False):
        if not component_types:
            raise StopAsyncIteration

        if include_subclasses:
            for entity in self.entities:
                if all([await entity.get_component(component_type, include_subclasses) for component_type in
                        component_types]):
                    yield entity
        else:
            entities = set(self.component_to_entities.get(component_types[0], []))
            for component_type in component_types[1:]:
                entities &= set(self.component_to_entities.get(component_type, []))
            for entity in list(entities):
                yield entity

    async def remove_component_from_entity(self, entity, component_type):
        entity.components.pop(component_type, None)
        self.component_to_entities[component_type].remove(entity)
        if not entity.components:
            self.entities.remove(entity)
