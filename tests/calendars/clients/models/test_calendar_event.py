import json

from dashboard.src.calendars.clients.models.calendar_event import CalendarEvent


class TestCalendarEventDataclass:
    """Tests for the client-side CalendarEvent dataclass."""

    def test_create_event(self):
        """Test creating a CalendarEvent instance."""
        event = CalendarEvent(
            uid="test-uid-123",
            calendar="Home",
            summary="Test Event",
            recurring=False,
            start_time="2025-08-15T10:00:00",
            end_time="2025-08-15T11:00:00",
        )
        assert event.uid == "test-uid-123"
        assert event.calendar == "Home"
        assert event.summary == "Test Event"
        assert event.recurring is False
        assert event.start_time == "2025-08-15T10:00:00"
        assert event.end_time == "2025-08-15T11:00:00"

    def test_to_dict(self):
        """Test converting event to dictionary."""
        event = CalendarEvent(
            uid="uid-1",
            calendar="Work",
            summary="Meeting",
            recurring=True,
            start_time="2025-08-15T09:00:00",
            end_time="2025-08-15T10:00:00",
        )
        result = event.to_dict()
        assert result == {
            "uid": "uid-1",
            "calendar": "Work",
            "summary": "Meeting",
            "recurring": True,
            "start_time": "2025-08-15T09:00:00",
            "end_time": "2025-08-15T10:00:00",
        }

    def test_to_json(self):
        """Test converting event to JSON string."""
        event = CalendarEvent(
            uid="uid-2",
            calendar="Home",
            summary="Dinner",
            recurring=False,
            start_time="2025-08-15T18:00:00",
            end_time="2025-08-15T19:00:00",
        )
        result = event.to_json()
        parsed = json.loads(result)
        assert parsed["uid"] == "uid-2"
        assert parsed["summary"] == "Dinner"
        assert parsed["recurring"] is False

    def test_to_json_roundtrip(self):
        """Test that to_json output can be parsed back to match to_dict."""
        event = CalendarEvent(
            uid="uid-3",
            calendar="Personal",
            summary="Gym",
            recurring=True,
            start_time="2025-08-15T07:00:00",
            end_time="2025-08-15T08:00:00",
        )
        assert json.loads(event.to_json()) == event.to_dict()

    def test_recurring_event(self):
        """Test creating a recurring event."""
        event = CalendarEvent(
            uid="uid-4_2025-08-15T10:00:00",
            calendar="Home",
            summary="Weekly Standup",
            recurring=True,
            start_time="2025-08-15T10:00:00",
            end_time="2025-08-15T10:30:00",
        )
        assert event.recurring is True
        assert "_" in event.uid
