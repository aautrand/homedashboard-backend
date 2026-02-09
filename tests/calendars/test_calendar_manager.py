import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from dashboard.src.calendars.calendar_manager import CalendarEventManager
from dashboard.src.calendars.models.calendar_event import CalendarEvent


def _make_db_event(
    id=1,
    uid="uid-1",
    calendar="Home",
    summary="Test Event",
    recurring=False,
    start_time=None,
    end_time=None,
    notified_at=None,
):
    """Helper to create a mock CalendarEvent ORM object."""
    event = MagicMock(spec=CalendarEvent)
    event.id = id
    event.uid = uid
    event.calendar = calendar
    event.summary = summary
    event.recurring = recurring
    event.start_time = start_time or datetime(2025, 8, 15, 10, 0, 0)
    event.end_time = end_time or datetime(2025, 8, 15, 11, 0, 0)
    event.notified_at = notified_at
    return event


def _make_caldav_json(
    uid="uid-1",
    calendar="Home",
    summary="Test Event",
    recurring=False,
    start_time="2025-08-15T10:00:00",
    end_time="2025-08-15T11:00:00",
):
    """Helper to create a CalDAV event JSON string."""
    return json.dumps({
        "uid": uid,
        "calendar": calendar,
        "summary": summary,
        "recurring": recurring,
        "start_time": start_time,
        "end_time": end_time,
    })


class TestCalendarEventManagerInit:
    """Tests for CalendarEventManager initialization."""

    def test_init_stores_db(self):
        """Test that the manager stores the db session."""
        mock_db = MagicMock()
        manager = CalendarEventManager(mock_db)
        assert manager.db is mock_db


class TestCalendarEventManagerSync:
    """Tests for CalendarEventManager sync_events."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def manager(self, mock_db):
        return CalendarEventManager(mock_db)

    @patch("dashboard.src.calendars.calendar_manager.get_calendar_client")
    def test_sync_inserts_new_events(self, mock_get_client, manager, mock_db):
        """Test that sync_events inserts events not in the database."""
        mock_client = MagicMock()
        mock_client.get_today_events.return_value = [
            _make_caldav_json(uid="new-uid", summary="New Event"),
        ]
        mock_get_client.return_value = mock_client

        # No existing events
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        start = datetime(2025, 8, 15, 0, 0, 0)
        end = datetime(2025, 8, 15, 23, 59, 59)

        result = manager.sync_events(["Home"], start, end)

        assert result["inserted"] == 1
        assert result["updated"] == 0
        assert result["deleted"] == 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    @patch("dashboard.src.calendars.calendar_manager.get_calendar_client")
    def test_sync_updates_changed_events(self, mock_get_client, manager, mock_db):
        """Test that sync_events updates events that have changed."""
        mock_client = MagicMock()
        mock_client.get_today_events.return_value = [
            _make_caldav_json(uid="existing-uid", summary="Updated Summary"),
        ]
        mock_get_client.return_value = mock_client

        # Existing event with different summary
        existing = _make_db_event(uid="existing-uid", summary="Old Summary")
        mock_db.execute.return_value.scalars.return_value.all.return_value = [existing]

        start = datetime(2025, 8, 15, 0, 0, 0)
        end = datetime(2025, 8, 15, 23, 59, 59)

        result = manager.sync_events(["Home"], start, end)

        assert result["updated"] == 1
        assert result["inserted"] == 0
        assert existing.summary == "Updated Summary"

    @patch("dashboard.src.calendars.calendar_manager.get_calendar_client")
    def test_sync_deletes_removed_events_in_range(self, mock_get_client, manager, mock_db):
        """Test that sync_events deletes events no longer in CalDAV within range."""
        mock_client = MagicMock()
        mock_client.get_today_events.return_value = []
        mock_get_client.return_value = mock_client

        start = datetime(2025, 8, 15, 0, 0, 0)
        end = datetime(2025, 8, 15, 23, 59, 59)

        # Existing event within the sync range
        existing = _make_db_event(
            uid="deleted-uid",
            start_time=datetime(2025, 8, 15, 10, 0, 0),
        )

        # First call: _get_events_by_uids (empty because no CalDAV UIDs)
        # Second call: _get_events_in_range (for total count)
        mock_db.execute.return_value.scalars.return_value.all.side_effect = [
            [],  # _get_events_by_uids
            [],  # _get_events_in_range
        ]

        result = manager.sync_events(["Home"], start, end)

        assert result["deleted"] == 0  # No events to match since CalDAV returns nothing

    @patch("dashboard.src.calendars.calendar_manager.get_calendar_client")
    def test_sync_no_changes(self, mock_get_client, manager, mock_db):
        """Test sync when events match exactly - no inserts, updates, or deletes."""
        mock_client = MagicMock()
        mock_client.get_today_events.return_value = [
            _make_caldav_json(uid="uid-1", summary="Same Event"),
        ]
        mock_get_client.return_value = mock_client

        existing = _make_db_event(
            uid="uid-1",
            summary="Same Event",
            calendar="Home",
            recurring=False,
            start_time=datetime(2025, 8, 15, 10, 0, 0),
            end_time=datetime(2025, 8, 15, 11, 0, 0),
        )
        mock_db.execute.return_value.scalars.return_value.all.return_value = [existing]

        start = datetime(2025, 8, 15, 0, 0, 0)
        end = datetime(2025, 8, 15, 23, 59, 59)

        result = manager.sync_events(["Home"], start, end)

        assert result["inserted"] == 0
        assert result["updated"] == 0
        mock_db.add.assert_not_called()

    @patch("dashboard.src.calendars.calendar_manager.get_calendar_client")
    def test_sync_empty_caldav(self, mock_get_client, manager, mock_db):
        """Test sync when CalDAV returns no events."""
        mock_client = MagicMock()
        mock_client.get_today_events.return_value = []
        mock_get_client.return_value = mock_client

        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        start = datetime(2025, 8, 15, 0, 0, 0)
        end = datetime(2025, 8, 15, 23, 59, 59)

        result = manager.sync_events(["Home"], start, end)

        assert result["inserted"] == 0
        assert result["updated"] == 0
        assert result["deleted"] == 0


class TestCalendarEventManagerQueries:
    """Tests for CalendarEventManager query methods."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def manager(self, mock_db):
        return CalendarEventManager(mock_db)

    def test_get_events_for_date(self, manager, mock_db):
        """Test getting events for a specific date."""
        mock_events = [_make_db_event()]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_events

        result = manager.get_events_for_date(date(2025, 8, 15))

        assert result == mock_events
        mock_db.execute.assert_called_once()

    def test_get_events_starting_between(self, manager, mock_db):
        """Test getting events starting in a time window."""
        mock_events = [_make_db_event()]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_events

        start = datetime(2025, 8, 15, 9, 0, 0)
        end = datetime(2025, 8, 15, 11, 0, 0)
        result = manager.get_events_starting_between(start, end)

        assert result == mock_events

    def test_get_all_events(self, manager, mock_db):
        """Test getting all stored events."""
        mock_events = [_make_db_event(id=1), _make_db_event(id=2)]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_events

        result = manager.get_all_events()

        assert len(result) == 2

    def test_get_event_by_uid(self, manager, mock_db):
        """Test getting an event by UID."""
        mock_event = _make_db_event(uid="specific-uid")
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_event

        result = manager.get_event_by_uid("specific-uid")

        assert result is mock_event

    def test_get_event_by_uid_not_found(self, manager, mock_db):
        """Test getting a non-existent event by UID."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = manager.get_event_by_uid("nonexistent")

        assert result is None

    def test_get_next_timed_event_skips_all_day(self, manager, mock_db):
        """Test that get_next_timed_event skips all-day events (midnight start)."""
        all_day = _make_db_event(
            id=1, summary="All Day", start_time=datetime(2025, 8, 16, 0, 0, 0)
        )
        timed = _make_db_event(
            id=2, summary="Meeting", start_time=datetime(2025, 8, 16, 14, 0, 0)
        )
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            all_day, timed
        ]

        result = manager.get_next_timed_event()

        assert result is timed

    def test_get_next_timed_event_none_available(self, manager, mock_db):
        """Test get_next_timed_event returns None when all events are all-day."""
        all_day = _make_db_event(
            summary="All Day", start_time=datetime(2025, 8, 16, 0, 0, 0)
        )
        mock_db.execute.return_value.scalars.return_value.all.return_value = [all_day]

        result = manager.get_next_timed_event()

        assert result is None

    def test_get_next_timed_event_empty(self, manager, mock_db):
        """Test get_next_timed_event returns None when no events exist."""
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        result = manager.get_next_timed_event()

        assert result is None

    def test_get_unnotified_events_starting_soon(self, manager, mock_db):
        """Test getting unnotified events starting soon."""
        timed_event = _make_db_event(
            start_time=datetime(2025, 8, 15, 10, 30, 0),
            notified_at=None,
        )
        mock_db.execute.return_value.scalars.return_value.all.return_value = [timed_event]

        result = manager.get_unnotified_events_starting_soon(minutes=15)

        assert len(result) == 1
        assert result[0] is timed_event

    def test_get_unnotified_events_filters_all_day(self, manager, mock_db):
        """Test that get_unnotified_events filters out all-day events."""
        all_day = _make_db_event(
            start_time=datetime(2025, 8, 15, 0, 0, 0),
            notified_at=None,
        )
        mock_db.execute.return_value.scalars.return_value.all.return_value = [all_day]

        result = manager.get_unnotified_events_starting_soon(minutes=15)

        assert len(result) == 0

    def test_mark_event_notified(self, manager, mock_db):
        """Test marking an event as notified."""
        mock_event = _make_db_event(id=5)
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_event

        manager.mark_event_notified(5)

        assert mock_event.notified_at is not None
        mock_db.commit.assert_called_once()

    def test_mark_event_notified_not_found(self, manager, mock_db):
        """Test marking a non-existent event as notified does nothing."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        manager.mark_event_notified(999)

        mock_db.commit.assert_not_called()

    @patch("dashboard.src.calendars.calendar_manager.get_calendar_client")
    def test_get_upcoming_events(self, mock_get_client, manager, mock_db):
        """Test getting upcoming events within default 10 minutes."""
        mock_events = [_make_db_event()]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_events

        result = manager.get_upcoming_events()

        assert result == mock_events


class TestCalendarEventManagerPrivateHelpers:
    """Tests for private helper methods."""

    @pytest.fixture
    def manager(self):
        return CalendarEventManager(MagicMock())

    def test_parse_datetime_iso_format(self, manager):
        """Test parsing a full ISO datetime string."""
        result = manager._parse_datetime("2025-08-15T10:30:00")
        assert result == datetime(2025, 8, 15, 10, 30, 0)

    def test_parse_datetime_date_only(self, manager):
        """Test parsing a date-only string (treated as midnight)."""
        result = manager._parse_datetime("2025-08-15")
        assert result == datetime(2025, 8, 15, 0, 0, 0)

    def test_parse_datetime_with_timezone_strips_tz(self, manager):
        """Test that timezone info is stripped from the result."""
        result = manager._parse_datetime("2025-08-15T10:30:00+05:00")
        assert result.tzinfo is None
        assert result == datetime(2025, 8, 15, 10, 30, 0)

    def test_datetimes_differ_same(self, manager):
        """Test that identical datetimes are not different."""
        dt = datetime(2025, 8, 15, 10, 0, 0)
        assert manager._datetimes_differ(dt, dt) is False

    def test_datetimes_differ_different(self, manager):
        """Test that different datetimes are detected."""
        dt1 = datetime(2025, 8, 15, 10, 0, 0)
        dt2 = datetime(2025, 8, 15, 11, 0, 0)
        assert manager._datetimes_differ(dt1, dt2) is True

    def test_datetimes_differ_tz_aware_vs_naive(self, manager):
        """Test comparing timezone-aware and naive datetimes with same time."""
        naive = datetime(2025, 8, 15, 10, 0, 0)
        aware = datetime(2025, 8, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert manager._datetimes_differ(naive, aware) is False

    def test_event_changed_same(self, manager):
        """Test _event_changed returns False when nothing changed."""
        db_event = _make_db_event(
            summary="Test",
            calendar="Home",
            recurring=False,
            start_time=datetime(2025, 8, 15, 10, 0, 0),
            end_time=datetime(2025, 8, 15, 11, 0, 0),
        )
        caldav_data = {
            "summary": "Test",
            "calendar": "Home",
            "recurring": False,
            "start_time": "2025-08-15T10:00:00",
            "end_time": "2025-08-15T11:00:00",
        }
        assert manager._event_changed(db_event, caldav_data) is False

    def test_event_changed_summary(self, manager):
        """Test _event_changed detects summary change."""
        db_event = _make_db_event(summary="Old")
        caldav_data = {
            "summary": "New",
            "calendar": "Home",
            "recurring": False,
            "start_time": "2025-08-15T10:00:00",
            "end_time": "2025-08-15T11:00:00",
        }
        assert manager._event_changed(db_event, caldav_data) is True

    def test_event_changed_calendar(self, manager):
        """Test _event_changed detects calendar change."""
        db_event = _make_db_event(calendar="Home")
        caldav_data = {
            "summary": "Test Event",
            "calendar": "Work",
            "recurring": False,
            "start_time": "2025-08-15T10:00:00",
            "end_time": "2025-08-15T11:00:00",
        }
        assert manager._event_changed(db_event, caldav_data) is True

    def test_event_changed_recurring(self, manager):
        """Test _event_changed detects recurring flag change."""
        db_event = _make_db_event(recurring=False)
        caldav_data = {
            "summary": "Test Event",
            "calendar": "Home",
            "recurring": True,
            "start_time": "2025-08-15T10:00:00",
            "end_time": "2025-08-15T11:00:00",
        }
        assert manager._event_changed(db_event, caldav_data) is True

    def test_event_changed_start_time(self, manager):
        """Test _event_changed detects start_time change."""
        db_event = _make_db_event(start_time=datetime(2025, 8, 15, 10, 0, 0))
        caldav_data = {
            "summary": "Test Event",
            "calendar": "Home",
            "recurring": False,
            "start_time": "2025-08-15T12:00:00",
            "end_time": "2025-08-15T11:00:00",
        }
        assert manager._event_changed(db_event, caldav_data) is True

    def test_get_events_by_uids_empty(self, manager):
        """Test _get_events_by_uids with empty list returns empty."""
        result = manager._get_events_by_uids([])
        assert result == []

    def test_insert_event(self, manager):
        """Test _insert_event creates and adds a CalendarEvent."""
        caldav_data = {
            "uid": "new-uid",
            "calendar": "Home",
            "summary": "New Event",
            "recurring": False,
            "start_time": "2025-08-15T10:00:00",
            "end_time": "2025-08-15T11:00:00",
        }
        result = manager._insert_event(caldav_data)

        assert isinstance(result, CalendarEvent)
        assert result.uid == "new-uid"
        assert result.summary == "New Event"
        manager.db.add.assert_called_once_with(result)

    def test_update_event(self, manager):
        """Test _update_event modifies an existing event."""
        db_event = MagicMock(spec=CalendarEvent)
        caldav_data = {
            "summary": "Updated",
            "calendar": "Work",
            "recurring": True,
            "start_time": "2025-08-15T14:00:00",
            "end_time": "2025-08-15T15:00:00",
        }

        manager._update_event(db_event, caldav_data)

        assert db_event.summary == "Updated"
        assert db_event.calendar == "Work"
        assert db_event.recurring is True