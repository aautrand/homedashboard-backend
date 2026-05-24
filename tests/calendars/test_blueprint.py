import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.calendars import calendar


@pytest.fixture
def app():
    """Create a Flask application for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["MAIN_CALENDAR"] = "Home"
    app.config["message_broker_client"] = MagicMock()
    return app


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def client(app, mock_db):
    """Create a test client with the calendar blueprint and mocked db."""
    app.register_blueprint(calendar)

    @app.before_request
    def inject_db():
        from flask import request

        request.db = mock_db

    return app.test_client()


class TestTextCalendarEndpoint:
    """Tests for GET /calendar/text."""

    @patch("dashboard.src.calendars.get_text_calendar")
    def test_returns_text_calendar(self, mock_get_cal, client):
        """Test successful text calendar retrieval."""
        mock_get_cal.return_value = "   August 2025\nSu Mo Tu..."
        response = client.get("/calendar/text")

        assert response.status_code == 200
        data = response.get_json()
        assert "calendar" in data
        assert "August 2025" in data["calendar"]

    def test_post_not_allowed(self, client):
        """Test POST to /calendar/text returns 405."""
        response = client.post("/calendar/text")
        assert response.status_code == 405


class TestCurrentEventsEndpoint:
    """Tests for GET /calendar/events."""

    @patch("dashboard.src.calendars.get_calendar_client")
    def test_returns_events(self, mock_get_client, client):
        """Test successful events retrieval from CalDAV."""
        mock_client = MagicMock()
        mock_client.get_today_events.return_value = [
            '{"uid": "1", "summary": "Meeting"}',
        ]
        mock_get_client.return_value = mock_client

        response = client.get("/calendar/events")

        assert response.status_code == 200
        data = response.get_json()
        assert "events" in data
        assert len(data["events"]) == 1

    @patch("dashboard.src.calendars.get_calendar_client")
    def test_returns_empty_list_when_no_events(self, mock_get_client, client):
        """Test empty list when no events today."""
        mock_client = MagicMock()
        mock_client.get_today_events.return_value = []
        mock_get_client.return_value = mock_client

        response = client.get("/calendar/events")

        assert response.status_code == 200
        data = response.get_json()
        assert data["events"] == []


class TestSyncCalendarEndpoint:
    """Tests for POST /calendar/sync."""

    @patch("dashboard.src.calendars.CalendarEventManager")
    def test_sync_returns_result(self, mock_manager_cls, client, app):
        """Test successful calendar sync."""
        mock_manager = MagicMock()
        mock_manager.sync_events.return_value = {
            "inserted": 2,
            "updated": 1,
            "deleted": 0,
            "total": 3,
        }
        mock_manager_cls.return_value = mock_manager

        response = client.post("/calendar/sync")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["sync_result"]["inserted"] == 2
        assert data["sync_result"]["total"] == 3

    def test_get_not_allowed(self, client):
        """Test GET to /calendar/sync returns 405."""
        response = client.get("/calendar/sync")
        assert response.status_code == 405


class TestStoredEventsEndpoint:
    """Tests for GET /calendar/events/stored."""

    @patch("dashboard.src.calendars.CalendarEventManager")
    def test_returns_stored_events(self, mock_manager_cls, client):
        """Test retrieving stored events from database."""
        mock_event = MagicMock()
        mock_event.to_dict.return_value = {
            "id": 1,
            "uid": "uid-1",
            "summary": "Stored Event",
        }
        mock_manager = MagicMock()
        mock_manager.get_events_for_date.return_value = [mock_event]
        mock_manager_cls.return_value = mock_manager

        response = client.get("/calendar/events/stored")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["events"]) == 1
        assert data["events"][0]["summary"] == "Stored Event"

    @patch("dashboard.src.calendars.CalendarEventManager")
    def test_returns_empty_when_no_stored_events(self, mock_manager_cls, client):
        """Test empty response when no stored events."""
        mock_manager = MagicMock()
        mock_manager.get_events_for_date.return_value = []
        mock_manager_cls.return_value = mock_manager

        response = client.get("/calendar/events/stored")

        assert response.status_code == 200
        data = response.get_json()
        assert data["events"] == []


class TestPrintNextEventEndpoint:
    """Tests for POST /calendar/events/print-next."""

    @patch("dashboard.src.calendars.PrintManager")
    @patch("dashboard.src.calendars.CalendarEventManager")
    def test_prints_next_event(self, mock_manager_cls, mock_print_mgr, client, app):
        """Test printing the next timed event."""
        mock_event = MagicMock()
        mock_event.summary = "Upcoming Meeting"
        mock_event.start_time.strftime.return_value = "14:00"
        mock_event.to_dict.return_value = {"summary": "Upcoming Meeting"}

        mock_manager = MagicMock()
        mock_manager.get_next_timed_event.return_value = mock_event
        mock_manager_cls.return_value = mock_manager

        mock_print_mgr.print_event.return_value = {"data": "formatted"}

        response = client.post("/calendar/events/print-next")

        assert response.status_code == 200
        data = response.get_json()
        assert data["printed"] is True
        assert data["event"]["summary"] == "Upcoming Meeting"
        app.config["message_broker_client"].send_message.assert_called_once()

    @patch("dashboard.src.calendars.CalendarEventManager")
    def test_no_upcoming_events(self, mock_manager_cls, client):
        """Test response when no upcoming timed events."""
        mock_manager = MagicMock()
        mock_manager.get_next_timed_event.return_value = None
        mock_manager_cls.return_value = mock_manager

        response = client.post("/calendar/events/print-next")

        assert response.status_code == 200
        data = response.get_json()
        assert data["printed"] is False
        assert "No upcoming" in data["message"]


class TestNotifyUpcomingEventsEndpoint:
    """Tests for POST /calendar/events/notify-upcoming."""

    @patch("dashboard.src.calendars.PrintManager")
    @patch("dashboard.src.calendars.CalendarEventManager")
    def test_notifies_upcoming_events(
        self, mock_manager_cls, mock_print_mgr, client, app
    ):
        """Test notifying and printing upcoming events."""
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.to_dict.return_value = {"id": 1, "summary": "Soon"}

        mock_manager = MagicMock()
        mock_manager.get_unnotified_events_starting_soon.return_value = [mock_event]
        mock_manager_cls.return_value = mock_manager

        mock_print_mgr.print_event.return_value = {"data": "formatted"}

        response = client.post("/calendar/events/notify-upcoming")

        assert response.status_code == 200
        data = response.get_json()
        assert data["printed_count"] == 1
        assert len(data["events"]) == 1
        mock_manager.mark_event_notified.assert_called_once_with(1)

    @patch("dashboard.src.calendars.CalendarEventManager")
    def test_no_events_to_notify(self, mock_manager_cls, client):
        """Test response when no events need notification."""
        mock_manager = MagicMock()
        mock_manager.get_unnotified_events_starting_soon.return_value = []
        mock_manager_cls.return_value = mock_manager

        response = client.post("/calendar/events/notify-upcoming")

        assert response.status_code == 200
        data = response.get_json()
        assert data["printed_count"] == 0
        assert data["events"] == []

    @patch("dashboard.src.calendars.CalendarEventManager")
    def test_custom_minutes_parameter(self, mock_manager_cls, client):
        """Test custom minutes query parameter."""
        mock_manager = MagicMock()
        mock_manager.get_unnotified_events_starting_soon.return_value = []
        mock_manager_cls.return_value = mock_manager

        response = client.post("/calendar/events/notify-upcoming?minutes=30")

        assert response.status_code == 200
        mock_manager.get_unnotified_events_starting_soon.assert_called_once_with(
            minutes=30
        )

    @patch("dashboard.src.calendars.PrintManager")
    @patch("dashboard.src.calendars.CalendarEventManager")
    def test_notifies_multiple_events(
        self, mock_manager_cls, mock_print_mgr, client, app
    ):
        """Test notifying multiple upcoming events."""
        events = []
        for i in range(3):
            e = MagicMock()
            e.id = i
            e.to_dict.return_value = {"id": i, "summary": f"Event {i}"}
            events.append(e)

        mock_manager = MagicMock()
        mock_manager.get_unnotified_events_starting_soon.return_value = events
        mock_manager_cls.return_value = mock_manager
        mock_print_mgr.print_event.return_value = {"data": "formatted"}

        response = client.post("/calendar/events/notify-upcoming")

        data = response.get_json()
        assert data["printed_count"] == 3
        assert mock_manager.mark_event_notified.call_count == 3
        assert app.config["message_broker_client"].send_message.call_count == 3


class TestCreateTodoEndpoint:
    """Tests for POST /calendar/todo."""

    @patch("dashboard.src.calendars.TodoManager")
    def test_create_todo_success(self, mock_manager_cls, client):
        """Test creating a new todo."""
        mock_todo = MagicMock()
        mock_todo.to_dict.return_value = {
            "id": 1,
            "title": "Buy milk",
            "active": True,
        }
        mock_manager = MagicMock()
        mock_manager.add_todo.return_value = mock_todo
        mock_manager_cls.return_value = mock_manager

        response = client.post(
            "/calendar/todo",
            data=json.dumps({"title": "Buy milk"}),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["title"] == "Buy milk"
        assert data["active"] is True

    @patch("dashboard.src.calendars.TodoManager")
    def test_create_todo_with_active_false(self, mock_manager_cls, client):
        """Test creating a todo with active=False."""
        mock_todo = MagicMock()
        mock_todo.to_dict.return_value = {"id": 1, "title": "Old", "active": False}
        mock_manager = MagicMock()
        mock_manager.add_todo.return_value = mock_todo
        mock_manager_cls.return_value = mock_manager

        response = client.post(
            "/calendar/todo",
            data=json.dumps({"title": "Old", "active": False}),
            content_type="application/json",
        )

        assert response.status_code == 201
        mock_manager.add_todo.assert_called_once_with(title="Old", active=False)

    def test_create_todo_missing_title(self, client):
        """Test creating a todo without title returns 400."""
        response = client.post(
            "/calendar/todo",
            data=json.dumps({"active": True}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "title" in data["error"]

    def test_create_todo_no_body(self, client):
        """Test creating a todo with no JSON body returns 400."""
        response = client.post("/calendar/todo", content_type="application/json")

        assert response.status_code == 400


class TestGetTodosEndpoint:
    """Tests for GET /calendar/todo."""

    @patch("dashboard.src.calendars.TodoManager")
    def test_get_all_todos(self, mock_manager_cls, client):
        """Test getting all todos without filter."""
        mock_todo = MagicMock()
        mock_todo.to_dict.return_value = {"id": 1, "title": "Todo 1", "active": True}
        mock_manager = MagicMock()
        mock_manager.get_all_todos.return_value = [mock_todo]
        mock_manager_cls.return_value = mock_manager

        response = client.get("/calendar/todo")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        mock_manager.get_all_todos.assert_called_once()

    @patch("dashboard.src.calendars.TodoManager")
    def test_get_active_todos(self, mock_manager_cls, client):
        """Test filtering todos by active=true."""
        mock_manager = MagicMock()
        mock_manager.get_todos_by_status.return_value = []
        mock_manager_cls.return_value = mock_manager

        response = client.get("/calendar/todo?active=true")

        assert response.status_code == 200
        mock_manager.get_todos_by_status.assert_called_once_with(True)

    @patch("dashboard.src.calendars.TodoManager")
    def test_get_inactive_todos(self, mock_manager_cls, client):
        """Test filtering todos by active=false."""
        mock_manager = MagicMock()
        mock_manager.get_todos_by_status.return_value = []
        mock_manager_cls.return_value = mock_manager

        response = client.get("/calendar/todo?active=false")

        assert response.status_code == 200
        mock_manager.get_todos_by_status.assert_called_once_with(False)

    def test_get_todos_invalid_active_param(self, client):
        """Test invalid active parameter returns 400."""
        response = client.get("/calendar/todo?active=maybe")

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    @patch("dashboard.src.calendars.TodoManager")
    def test_get_todos_active_case_insensitive(self, mock_manager_cls, client):
        """Test that active param is case-insensitive (True/TRUE)."""
        mock_manager = MagicMock()
        mock_manager.get_todos_by_status.return_value = []
        mock_manager_cls.return_value = mock_manager

        response = client.get("/calendar/todo?active=True")

        assert response.status_code == 200
        mock_manager.get_todos_by_status.assert_called_once_with(True)


class TestGetSingleTodoEndpoint:
    """Tests for GET /calendar/todo/<id>."""

    @patch("dashboard.src.calendars.TodoManager")
    def test_get_todo_success(self, mock_manager_cls, client):
        """Test getting a single todo by ID."""
        mock_todo = MagicMock()
        mock_todo.to_dict.return_value = {"id": 1, "title": "Todo 1"}
        mock_manager = MagicMock()
        mock_manager.get_todo.return_value = mock_todo
        mock_manager_cls.return_value = mock_manager

        response = client.get("/calendar/todo/1")

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == 1

    @patch("dashboard.src.calendars.TodoManager")
    def test_get_todo_not_found(self, mock_manager_cls, client):
        """Test getting a non-existent todo returns 404."""
        mock_manager = MagicMock()
        mock_manager.get_todo.return_value = None
        mock_manager_cls.return_value = mock_manager

        response = client.get("/calendar/todo/999")

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data


class TestUpdateTodoEndpoint:
    """Tests for PUT /calendar/todo/<id>."""

    @patch("dashboard.src.calendars.TodoManager")
    def test_update_todo_success(self, mock_manager_cls, client):
        """Test updating a todo title (no completion, no print)."""
        mock_existing = MagicMock()
        mock_existing.active = True
        mock_todo = MagicMock()
        mock_todo.to_dict.return_value = {"id": 1, "title": "Updated", "active": True}
        mock_manager = MagicMock()
        mock_manager.get_todo.return_value = mock_existing
        mock_manager.update_todo.return_value = mock_todo
        mock_manager_cls.return_value = mock_manager

        response = client.put(
            "/calendar/todo/1",
            data=json.dumps({"title": "Updated"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "Updated"

    @patch("dashboard.src.calendars.TodoManager")
    def test_update_todo_not_found(self, mock_manager_cls, client):
        """Test updating a non-existent todo returns 404."""
        mock_manager = MagicMock()
        mock_manager.get_todo.return_value = None
        mock_manager_cls.return_value = mock_manager

        response = client.put(
            "/calendar/todo/999",
            data=json.dumps({"title": "Nope"}),
            content_type="application/json",
        )

        assert response.status_code == 404

    @patch("dashboard.src.calendars.PrintManager")
    @patch("dashboard.src.calendars.TodoManager")
    def test_update_todo_complete_triggers_print(
        self, mock_manager_cls, mock_print_mgr, client, app
    ):
        """Test that marking a todo complete sends it to the printer."""
        mock_existing = MagicMock()
        mock_existing.active = True
        mock_todo = MagicMock()
        mock_todo.to_dict.return_value = {"id": 1, "title": "Buy milk", "active": False}
        mock_manager = MagicMock()
        mock_manager.get_todo.return_value = mock_existing
        mock_manager.update_todo.return_value = mock_todo
        mock_manager_cls.return_value = mock_manager
        mock_print_mgr.print_todo.return_value = {"title": " To Dos ", "content": []}

        response = client.put(
            "/calendar/todo/1",
            data=json.dumps({"active": False}),
            content_type="application/json",
        )

        assert response.status_code == 200
        mock_print_mgr.print_todo.assert_called_once_with(mock_todo)
        app.config["message_broker_client"].send_message.assert_called_once()

    @patch("dashboard.src.calendars.PrintManager")
    @patch("dashboard.src.calendars.TodoManager")
    def test_update_todo_already_inactive_no_print(
        self, mock_manager_cls, mock_print_mgr, client, app
    ):
        """Test that updating an already-inactive todo does not trigger a print."""
        mock_existing = MagicMock()
        mock_existing.active = False
        mock_todo = MagicMock()
        mock_todo.to_dict.return_value = {"id": 1, "title": "Old task", "active": False}
        mock_manager = MagicMock()
        mock_manager.get_todo.return_value = mock_existing
        mock_manager.update_todo.return_value = mock_todo
        mock_manager_cls.return_value = mock_manager

        response = client.put(
            "/calendar/todo/1",
            data=json.dumps({"active": False}),
            content_type="application/json",
        )

        assert response.status_code == 200
        mock_print_mgr.print_todo.assert_not_called()
        app.config["message_broker_client"].send_message.assert_not_called()

    @patch("dashboard.src.calendars.PrintManager")
    @patch("dashboard.src.calendars.TodoManager")
    def test_update_todo_reactivate_no_print(
        self, mock_manager_cls, mock_print_mgr, client, app
    ):
        """Test that reactivating a todo (active=True) does not trigger a print."""
        mock_existing = MagicMock()
        mock_existing.active = False
        mock_todo = MagicMock()
        mock_todo.to_dict.return_value = {"id": 1, "title": "Task", "active": True}
        mock_manager = MagicMock()
        mock_manager.get_todo.return_value = mock_existing
        mock_manager.update_todo.return_value = mock_todo
        mock_manager_cls.return_value = mock_manager

        response = client.put(
            "/calendar/todo/1",
            data=json.dumps({"active": True}),
            content_type="application/json",
        )

        assert response.status_code == 200
        mock_print_mgr.print_todo.assert_not_called()

    def test_update_todo_empty_body(self, client):
        """Test updating a todo with empty JSON body returns 400."""
        response = client.put(
            "/calendar/todo/1",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestDeleteTodoEndpoint:
    """Tests for DELETE /calendar/todo/<id>."""

    @patch("dashboard.src.calendars.TodoManager")
    def test_delete_todo_success(self, mock_manager_cls, client):
        """Test deleting a todo."""
        mock_todo = MagicMock()
        mock_manager = MagicMock()
        mock_manager.delete_todo.return_value = mock_todo
        mock_manager_cls.return_value = mock_manager

        response = client.delete("/calendar/todo/1")

        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "deleted" in data["message"].lower()

    @patch("dashboard.src.calendars.TodoManager")
    def test_delete_todo_not_found(self, mock_manager_cls, client):
        """Test deleting a non-existent todo returns 404."""
        mock_manager = MagicMock()
        mock_manager.delete_todo.return_value = None
        mock_manager_cls.return_value = mock_manager

        response = client.delete("/calendar/todo/999")

        assert response.status_code == 404


class TestPrintTodoEndpoint:
    """Tests for POST /calendar/todo/<id>/print."""

    @patch("dashboard.src.calendars.PrintManager")
    @patch("dashboard.src.calendars.TodoManager")
    def test_print_todo_success(self, mock_manager_cls, mock_print_mgr, client, app):
        """Test printing a todo."""
        mock_todo = MagicMock()
        mock_manager = MagicMock()
        mock_manager.get_todo.return_value = mock_todo
        mock_manager_cls.return_value = mock_manager

        mock_print_mgr.print_todo.return_value = {"data": "formatted_todo"}

        response = client.post("/calendar/todo/1/print")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        mock_print_mgr.print_todo.assert_called_once_with(mock_todo)
        app.config["message_broker_client"].send_message.assert_called_once()

    @patch("dashboard.src.calendars.TodoManager")
    def test_print_todo_not_found(self, mock_manager_cls, client):
        """Test printing a non-existent todo returns 404."""
        mock_manager = MagicMock()
        mock_manager.get_todo.return_value = None
        mock_manager_cls.return_value = mock_manager

        response = client.post("/calendar/todo/999/print")

        assert response.status_code == 404


class TestCalendarBlueprintRegistration:
    """Tests for calendar blueprint registration."""

    def test_blueprint_has_correct_url_prefix(self):
        """Test calendar blueprint has /calendar URL prefix."""
        assert calendar.url_prefix == "/calendar"

    def test_blueprint_has_correct_name(self):
        """Test calendar blueprint has correct name."""
        assert calendar.name == "calendar"
