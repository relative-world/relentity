from typing import Callable, FrozenSet, Any
from weakref import WeakValueDictionary

from relentity.core import Component

class EntityMeta(type):
    """
    EntityMeta is a metaclass that allows the composition of Entities with components
    using square braces syntax. This metaclass enables the creation of new entity types
    with specified components implicitly added at instantiation time.

    Example usage:
        def get_spawn_point() -> Position:
            return Position(x=0, y=0)

        Entity[get_spawn_point, Velocity(vx=0, vy=0)]

    In this example, `get_spawn_point` is a callable that returns a Component instance,
    and `Velocity(vx=0, vy=0)` is a Component instance. The resulting type is a new entity
    type with these components added.

    The callable should take no arguments and annotate its return type to be an instance of a Component subclass.

    The square brace syntax does not instantiate the Entity itself. Instead, it creates a Entity subclass
    with the specified components. When an instance of this new type is created, the components
    are added to the entity as long as `super().__init__()` is called in the entity's `__init__` method.
    """

    def __getitem__(cls, components: Component | Callable | list[Component | Callable]) -> 'EntityMeta':
        """
        This method is called when square braces are used with the Entity class.
        It takes a list of components, which can be either Component instances or callables
        that return Component instances, and returns a new entity type with these components.

        Args:
            components (list[Component | Callable]): A list of components to be added to the entity.

        Returns:
            EntityMeta: A new entity type with the specified components.
        """
        # Convert single component to a tuple for consistent handling
        if not isinstance(components, tuple):
            components = (components,)

        # Create a frozen set of component classes to ensure immutability and uniqueness
        _component_classes: FrozenSet[Component | Callable] = frozenset(type(component) for component in components)

        class EntityWithComponents(cls):
            """
            A new entity type with the specified components added.

            This class inherits from the original entity class and adds the specified components
            during initialization.
            """

            def __init__(self, *args, **kwargs):
                """
                Initialize the new entity type and add the specified components.

                Args:
                    *args: Positional arguments for the entity's initialization.
                    **kwargs: Keyword arguments for the entity's initialization.
                """
                # Call the original entity's __init__ method
                super().__init__(*args, **kwargs)
                # Add each component to the entity
                for component in components:
                    if isinstance(component, Component):
                        # If the component is an instance of Component, add it directly
                        self.add_component_sync(component.model_copy())
                    elif callable(component):
                        # If the component is a callable, call it to get the Component instance and add it
                        self.add_component_sync(component())
                    else:
                        # Raise an error if the component is neither a Component instance nor a callable
                        raise TypeError("Component must be a Component instance or a callable")

        return EntityWithComponents
