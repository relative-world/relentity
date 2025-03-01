import pytest
from pydantic import ValidationError
from relentity.core.components import Component, Identity


class TestComponent:
    def test_component_is_base_model(self):
        """Test that Component is a subclass of BaseModel."""
        # Arrange & Act
        component = Component()

        # Assert
        assert isinstance(component, Component)

    def test_component_subclass_creation(self):
        """Test creating a custom component subclass."""

        # Arrange
        class CustomComponent(Component):
            value: int = 42

        # Act
        component = CustomComponent()

        # Assert
        assert isinstance(component, Component)
        assert component.value == 42


class TestIdentity:
    def test_identity_creation(self):
        """Test creating an Identity component."""
        # Arrange & Act
        identity = Identity(name="Test", description="A test identity")

        # Assert
        assert identity.name == "Test"
        assert identity.description == "A test identity"

    def test_identity_validation(self):
        """Test that Identity validates its fields."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            Identity(name=None, description="Missing name")
