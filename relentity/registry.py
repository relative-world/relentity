class Registry:
    def __init__(self):
        self.entities = []
        self.component_to_entities = {}

    def register_entity(self, entity):
        self.entities.append(entity)
        for component_type in entity.components:
            if component_type not in self.component_to_entities:
                self.component_to_entities[component_type] = []
            self.component_to_entities[component_type].append(entity)

    def get_entities_with_components(self, *component_types):
        if not component_types:
            return []
        entities = set(self.component_to_entities.get(component_types[0], []))
        for component_type in component_types[1:]:
            entities &= set(self.component_to_entities.get(component_type, []))
        return list(entities)
