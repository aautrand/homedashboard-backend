import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.learning.routes.reminders import reminders_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["message_broker_client"] = MagicMock()
    return app


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(app, mock_db):
    app.register_blueprint(reminders_bp, url_prefix="/learning")

    @app.before_request
    def inject_db():
        from flask import request

        request.db = mock_db

    return app.test_client()


class TestCreateReminder:

    @patch("dashboard.src.learning.routes.reminders.ReminderManager")
    def test_success(self, mock_cls, client):
        mock_r = MagicMock()
        mock_r.to_dict.return_value = {"id": 1, "title": "Water", "active": True}
        mock_cls.return_value.add_reminder.return_value = mock_r

        resp = client.post(
            "/learning/reminder",
            data=json.dumps({"title": "Water"}),
            content_type="application/json",
        )
        assert resp.status_code == 201

    def test_missing_title(self, client):
        resp = client.post(
            "/learning/reminder",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestGetReminders:

    @patch("dashboard.src.learning.routes.reminders.ReminderManager")
    def test_all(self, mock_cls, client):
        mock_r = MagicMock()
        mock_r.to_dict.return_value = {"id": 1}
        mock_cls.return_value.get_all_reminders.return_value = [mock_r]

        resp = client.get("/learning/reminder")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 1

    @patch("dashboard.src.learning.routes.reminders.ReminderManager")
    def test_active_true(self, mock_cls, client):
        mock_cls.return_value.get_reminders_by_status.return_value = []
        resp = client.get("/learning/reminder?active=true")
        assert resp.status_code == 200
        mock_cls.return_value.get_reminders_by_status.assert_called_once_with(True)

    @patch("dashboard.src.learning.routes.reminders.ReminderManager")
    def test_active_false(self, mock_cls, client):
        mock_cls.return_value.get_reminders_by_status.return_value = []
        resp = client.get("/learning/reminder?active=false")
        assert resp.status_code == 200
        mock_cls.return_value.get_reminders_by_status.assert_called_once_with(False)

    def test_invalid_active_param(self, client):
        resp = client.get("/learning/reminder?active=maybe")
        assert resp.status_code == 400


class TestGetReminder:

    @patch("dashboard.src.learning.routes.reminders.ReminderManager")
    def test_found(self, mock_cls, client):
        mock_r = MagicMock()
        mock_r.to_dict.return_value = {"id": 1}
        mock_cls.return_value.get_reminder.return_value = mock_r

        resp = client.get("/learning/reminder/1")
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.reminders.ReminderManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.get_reminder.return_value = None
        resp = client.get("/learning/reminder/999")
        assert resp.status_code == 404


class TestUpdateReminder:

    @patch("dashboard.src.learning.routes.reminders.ReminderManager")
    def test_success(self, mock_cls, client):
        mock_r = MagicMock()
        mock_r.to_dict.return_value = {"id": 1, "title": "Updated"}
        mock_cls.return_value.update_reminder.return_value = mock_r

        resp = client.put(
            "/learning/reminder/1",
            data=json.dumps({"title": "Updated"}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.reminders.ReminderManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.update_reminder.return_value = None
        resp = client.put(
            "/learning/reminder/999",
            data=json.dumps({"title": "X"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_no_data(self, client):
        resp = client.put("/learning/reminder/1", content_type="application/json")
        assert resp.status_code == 400


class TestDeleteReminder:

    @patch("dashboard.src.learning.routes.reminders.ReminderManager")
    def test_success(self, mock_cls, client):
        mock_cls.return_value.delete_reminder.return_value = MagicMock()
        resp = client.delete("/learning/reminder/1")
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.reminders.ReminderManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.delete_reminder.return_value = None
        resp = client.delete("/learning/reminder/999")
        assert resp.status_code == 404


class TestPrintReminder:

    @patch("dashboard.src.learning.routes.reminders.PrintManager")
    @patch("dashboard.src.learning.routes.reminders.ReminderManager")
    def test_success(self, mock_mgr_cls, mock_print_cls, client, app):
        mock_r = MagicMock()
        mock_mgr_cls.return_value.get_reminder.return_value = mock_r
        mock_print_cls.print_reminder.return_value = {"data": "formatted"}

        resp = client.post("/learning/reminder/1/print")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"
        app.config["message_broker_client"].send_message.assert_called_once()

    @patch("dashboard.src.learning.routes.reminders.ReminderManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.get_reminder.return_value = None
        resp = client.post("/learning/reminder/999/print")
        assert resp.status_code == 404
