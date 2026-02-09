from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.calendars.clients.ical_client import ICalClient


class TestICalClient:
    """Tests for the ICalClient CalDAV client."""

    @pytest.fixture
    def app(self):
        """Create a Flask app with test config."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["CALDAV_ICLOUD_URL"] = "https://caldav.example.com"
        app.config["APPLE_USER"] = "test@example.com"
        app.config["APPLE_DASHBOARD_SECRET"] = "test-secret"
        return app

    @patch("dashboard.src.calendars.clients.ical_client.DAVClient")
    def test_init_sets_credentials(self, mock_dav_client, app):
        """Test that ICalClient sets credentials from app config."""
        with app.app_context():
            client = ICalClient()
            assert client.BASE_URL == "https://caldav.example.com"
            assert client.username == "test@example.com"
            assert client.password == "test-secret"

    @patch("dashboard.src.calendars.clients.ical_client.DAVClient")
    def test_init_creates_dav_client(self, mock_dav_client, app):
        """Test that ICalClient creates a DAVClient with correct params."""
        with app.app_context():
            ICalClient()
            mock_dav_client.assert_called_once_with(
                url="https://caldav.example.com",
                username="test@example.com",
                password="test-secret",
            )

    @patch("dashboard.src.calendars.clients.ical_client.DAVClient")
    def test_get_raw_events_filters_by_calendar_name(self, mock_dav_client, app):
        """Test that get_raw_events only fetches from matching calendars."""
        with app.app_context():
            # Set up mock calendars
            cal_home = MagicMock()
            cal_home.name = "Home"
            cal_home.date_search.return_value = ["event1"]

            cal_work = MagicMock()
            cal_work.name = "Work"
            cal_work.date_search.return_value = ["event2"]

            cal_other = MagicMock()
            cal_other.name = "Other"

            mock_principal = MagicMock()
            mock_principal.calendars.return_value = [cal_home, cal_work, cal_other]
            mock_dav_client.return_value.principal.return_value = mock_principal

            client = ICalClient()
            result = client.get_raw_events(["Home", "Work"], "start", "end")

            assert len(result) == 2
            cal_home.date_search.assert_called_once_with("start", "end")
            cal_work.date_search.assert_called_once_with("start", "end")
            cal_other.date_search.assert_not_called()

    @patch("dashboard.src.calendars.clients.ical_client.DAVClient")
    def test_get_raw_events_no_matching_calendars(self, mock_dav_client, app):
        """Test get_raw_events returns empty when no calendars match."""
        with app.app_context():
            cal_other = MagicMock()
            cal_other.name = "Other"

            mock_principal = MagicMock()
            mock_principal.calendars.return_value = [cal_other]
            mock_dav_client.return_value.principal.return_value = mock_principal

            client = ICalClient()
            result = client.get_raw_events(["Home"], "start", "end")

            assert result == []

    @patch("dashboard.src.calendars.clients.ical_client.DAVClient")
    def test_get_raw_events_empty_principal(self, mock_dav_client, app):
        """Test get_raw_events when principal has no calendars."""
        with app.app_context():
            mock_principal = MagicMock()
            mock_principal.calendars.return_value = []
            mock_dav_client.return_value.principal.return_value = mock_principal

            client = ICalClient()
            result = client.get_raw_events(["Home"], "start", "end")

            assert result == []
