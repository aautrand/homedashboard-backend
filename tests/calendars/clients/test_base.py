from unittest.mock import patch

import pytest

from dashboard.src.calendars.clients.base import CalendarClient, get_calendar_client


class TestGetCalendarClient:
    """Tests for the get_calendar_client factory function."""

    def test_returns_ical_client_by_default(self):
        """Test that the default source returns an ICalClient."""
        from flask import Flask

        from dashboard.src.calendars.clients.ical_client import ICalClient

        app = Flask(__name__)
        app.config["CALDAV_ICLOUD_URL"] = "https://example.com"
        app.config["APPLE_USER"] = "user"
        app.config["APPLE_DASHBOARD_SECRET"] = "secret"

        with app.app_context():
            with patch("dashboard.src.calendars.clients.ical_client.DAVClient"):
                result = get_calendar_client("ical")
                assert isinstance(result, ICalClient)

    def test_unknown_source_raises_value_error(self):
        """Test that an unknown source raises ValueError."""
        with pytest.raises(ValueError, match="Unknown source: google"):
            get_calendar_client("google")

    def test_unknown_source_error_message(self):
        """Test that the error message includes the source name."""
        with pytest.raises(ValueError, match="fake_source"):
            get_calendar_client("fake_source")


class TestCalendarClientABC:
    """Tests for the CalendarClient abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Test that CalendarClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CalendarClient()

    def test_subclass_must_implement_get_raw_events(self):
        """Test that a subclass without get_raw_events raises TypeError."""

        class IncompleteClient(CalendarClient):
            pass

        with pytest.raises(TypeError):
            IncompleteClient()

    def test_subclass_with_get_raw_events_can_instantiate(self):
        """Test that a complete subclass can be instantiated."""

        class CompleteClient(CalendarClient):
            def get_raw_events(self, calendars, start, end):
                return []

        client = CompleteClient()
        assert client.get_raw_events([], None, None) == []
