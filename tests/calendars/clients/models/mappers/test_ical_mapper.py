import json
from unittest.mock import MagicMock, PropertyMock

from dashboard.src.calendars.clients.models.mappers.ical_mapper import (
    ICalCalendarSequentialEventMapper,
)


def _make_vevent(
    uid, summary, start_iso, end_iso, recurring=False, recurrence_id_val=None
):
    """Helper to create a mock vevent object."""
    vevent = MagicMock()
    vevent.uid.value = uid
    vevent.summary.value = summary
    vevent.dtstart.value.isoformat.return_value = start_iso
    vevent.dtend.value.isoformat.return_value = end_iso

    contents = {}
    if recurring and recurrence_id_val is not None:
        recurrence_id_mock = MagicMock()
        recurrence_id_mock.value.isoformat.return_value = recurrence_id_val
        contents["recurrence-id"] = [recurrence_id_mock]

    vevent.contents.keys.return_value = contents.keys()
    vevent.contents.get.side_effect = contents.get

    return vevent


def _make_caldav_event(vevent, calendar_name="Home"):
    """Helper to create a mock caldav event object."""
    event = MagicMock()
    event.vobject_instance.vevent = vevent
    event.parent.name = calendar_name
    return event


class TestICalCalendarSequentialEventMapper:
    """Tests for the ICalCalendarSequentialEventMapper."""

    def setup_method(self):
        self.mapper = ICalCalendarSequentialEventMapper()

    def test_map_empty_list(self):
        """Test mapping an empty list returns empty."""
        result = self.mapper.map([])
        assert result == []

    def test_map_single_event(self):
        """Test mapping a single non-recurring event."""
        vevent = _make_vevent(
            uid="uid-1",
            summary="Test Event",
            start_iso="2025-08-15T10:00:00",
            end_iso="2025-08-15T11:00:00",
        )
        caldav_event = _make_caldav_event(vevent, "Home")

        result = self.mapper.map([[caldav_event]])
        assert len(result) == 1

        parsed = json.loads(result[0])
        assert parsed["uid"] == "uid-1"
        assert parsed["calendar"] == "Home"
        assert parsed["summary"] == "Test Event"
        assert parsed["recurring"] is False
        assert parsed["start_time"] == "2025-08-15T10:00:00"
        assert parsed["end_time"] == "2025-08-15T11:00:00"

    def test_map_recurring_event(self):
        """Test mapping a recurring event appends recurrence-id to UID."""
        vevent = _make_vevent(
            uid="uid-recurring",
            summary="Weekly Meeting",
            start_iso="2025-08-15T09:00:00",
            end_iso="2025-08-15T10:00:00",
            recurring=True,
            recurrence_id_val="2025-08-15T09:00:00",
        )
        caldav_event = _make_caldav_event(vevent, "Work")

        result = self.mapper.map([[caldav_event]])
        assert len(result) == 1

        parsed = json.loads(result[0])
        assert parsed["uid"] == "uid-recurring_2025-08-15T09:00:00"
        assert parsed["recurring"] is True

    def test_map_multiple_calendars(self):
        """Test mapping events from multiple calendars."""
        vevent1 = _make_vevent(
            "uid-1", "Event A", "2025-08-15T10:00:00", "2025-08-15T11:00:00"
        )
        vevent2 = _make_vevent(
            "uid-2", "Event B", "2025-08-15T14:00:00", "2025-08-15T15:00:00"
        )

        cal1_events = [_make_caldav_event(vevent1, "Home")]
        cal2_events = [_make_caldav_event(vevent2, "Chores")]

        result = self.mapper.map([cal1_events, cal2_events])
        assert len(result) == 2

        parsed_0 = json.loads(result[0])
        parsed_1 = json.loads(result[1])
        assert parsed_0["calendar"] == "Home"
        assert parsed_1["calendar"] == "Chores"

    def test_map_multiple_events_same_calendar(self):
        """Test mapping multiple events from the same calendar."""
        vevent1 = _make_vevent(
            "uid-1", "Morning", "2025-08-15T08:00:00", "2025-08-15T09:00:00"
        )
        vevent2 = _make_vevent(
            "uid-2", "Afternoon", "2025-08-15T14:00:00", "2025-08-15T15:00:00"
        )

        result = self.mapper.map(
            [[_make_caldav_event(vevent1), _make_caldav_event(vevent2)]]
        )
        assert len(result) == 2

    def test_map_empty_calendar(self):
        """Test mapping when one calendar has no events."""
        vevent = _make_vevent(
            "uid-1", "Event", "2025-08-15T10:00:00", "2025-08-15T11:00:00"
        )
        result = self.mapper.map([[], [_make_caldav_event(vevent)]])
        assert len(result) == 1

    def test_map_returns_json_strings(self):
        """Test that each element in the result is a valid JSON string."""
        vevent = _make_vevent(
            "uid-1", "Event", "2025-08-15T10:00:00", "2025-08-15T11:00:00"
        )
        result = self.mapper.map([[_make_caldav_event(vevent)]])

        for item in result:
            assert isinstance(item, str)
            parsed = json.loads(item)
            assert "uid" in parsed
            assert "summary" in parsed
