from .registry import Registry

class System:
    def __init__(self, registry: Registry):
        """
        Initializes the System with a registry.

        Args:
            registry (Registry): The registry to be used by the system.
        """
        self.registry = registry

    async def update(self) -> None:
        """
        Updates the system. This method should be overridden by subclasses.

        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """
        raise NotImplementedError
