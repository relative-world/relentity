from relentity.core.events import Event


class TestEvent:
    def test_event_initialization(self):
        """Test Event initialization with name and data."""
        # Arrange & Act
        event = Event("test.event", {"value": 42})

        # Assert
        assert event.name == "test.event"
        assert event.data == {"value": 42}

    def test_event_without_data(self):
        """Test Event initialization without data."""
        # Arrange & Act
        event = Event("test.event")

        # Assert
        assert event.name == "test.event"
        assert event.data is None
