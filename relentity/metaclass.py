from typing import Callable

from relentity.components import Component


class EntityMeta(type):
    def __getitem__(cls, components: list[Component]):
        _component_classes: list[type[Component] | Callable] = set(type(component) for component in components)

        class EntityWithComponents(cls):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for component in components:
                    if isinstance(component, Component):
                        self.add_component_sync(component.model_copy())
                    elif callable(component):
                        self.add_component_sync(component())
                    else:
                        raise TypeError("Component must be a Component instance or a callable")

            def __subclasscheck__(self, subclass):
                return super().__subclasscheck__(subclass) and all(
                    issubclass(component, subclass) for component in components
                )

        return EntityWithComponents
