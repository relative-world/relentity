import pytest

from relentity.core.systems import System


class TestSystem:
    def test_system_initialization(self, registry):
        """Test initializing a system with a registry."""
        # Arrange & Act
        system = System(registry)

        # Assert
        assert system.registry == registry

    @pytest.mark.asyncio
    async def test_update_not_implemented(self, registry):
        """Test that the base System class raises NotImplementedError."""
        # Arrange
        system = System(registry)

        # Act & Assert
        with pytest.raises(NotImplementedError):
            await system.update()


class CustomSystem(System):
    """A custom system implementation for testing."""

    def __init__(self, registry):
        super().__init__(registry)
        self.updated = False

    async def update(self, delta_time: float = 0) -> None:
        self.updated = True


@pytest.mark.asyncio
async def test_custom_system(registry):
    """Test a custom system implementation."""
    # Arrange
    system = CustomSystem(registry)

    # Act
    await system.update()

    # Assert
    assert system.updated
