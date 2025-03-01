from typing import Callable, FrozenSet, Any
from weakref import WeakValueDictionary

from relentity.core import Component


class EntityMeta(type):

    def __getitem__(cls, components: list[Component | Callable]) -> 'EntityMeta':
        _component_classes: FrozenSet[Component | Callable] = frozenset(type(component) for component in components)

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

        return EntityWithComponents
