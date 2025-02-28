class EntityMeta(type):
    def __getitem__(cls, components):
        class EntityWithComponents(cls):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for component in components:
                    self.add_component(component)

        return EntityWithComponents
