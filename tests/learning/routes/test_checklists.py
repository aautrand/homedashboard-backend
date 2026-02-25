import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.learning.routes.checklists import checklists_bp


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
    app.register_blueprint(checklists_bp, url_prefix="/learning")

    @app.before_request
    def inject_db():
        from flask import request
        request.db = mock_db

    return app.test_client()


class TestCreateChecklist:

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_success(self, mock_cls, client):
        mock_cl = MagicMock()
        mock_cl.to_dict.return_value = {"id": 1, "title": "Morning", "items": ["A"]}
        mock_cls.return_value.add_checklist.return_value = mock_cl

        resp = client.post(
            "/learning/checklists",
            data=json.dumps({"title": "Morning", "items": ["A"]}),
            content_type="application/json",
        )
        assert resp.status_code == 201

    def test_missing_title(self, client):
        resp = client.post(
            "/learning/checklists",
            data=json.dumps({"items": ["A"]}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestGetChecklists:

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_all(self, mock_cls, client):
        mock_cl = MagicMock()
        mock_cl.to_dict.return_value = {"id": 1, "title": "CL"}
        mock_cls.return_value.get_all_checklists.return_value = [mock_cl]

        resp = client.get("/learning/checklists")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 1


class TestGetChecklist:

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_found(self, mock_cls, client):
        mock_cl = MagicMock()
        mock_cl.to_dict.return_value = {"id": 1, "title": "CL", "notes": []}
        mock_cls.return_value.get_checklist.return_value = mock_cl

        resp = client.get("/learning/checklists/1")
        assert resp.status_code == 200
        assert "notes" in resp.get_json()

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.get_checklist.return_value = None
        resp = client.get("/learning/checklists/999")
        assert resp.status_code == 404


class TestUpdateChecklist:

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_success(self, mock_cls, client):
        mock_cl = MagicMock()
        mock_cl.to_dict.return_value = {"id": 1, "title": "Updated"}
        mock_cls.return_value.update_checklist.return_value = mock_cl

        resp = client.put(
            "/learning/checklists/1",
            data=json.dumps({"title": "Updated"}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.update_checklist.return_value = None
        resp = client.put(
            "/learning/checklists/999",
            data=json.dumps({"title": "X"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_no_data(self, client):
        resp = client.put("/learning/checklists/1", content_type="application/json")
        assert resp.status_code == 400


class TestDeleteChecklist:

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_success(self, mock_cls, client):
        mock_cls.return_value.delete_checklist.return_value = MagicMock()
        resp = client.delete("/learning/checklists/1")
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.delete_checklist.return_value = None
        resp = client.delete("/learning/checklists/999")
        assert resp.status_code == 404


class TestPrintChecklist:

    @patch("dashboard.src.learning.routes.checklists.PrintManager")
    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_success(self, mock_mgr_cls, mock_print_cls, client, app):
        mock_cl = MagicMock()
        mock_mgr_cls.return_value.get_checklist.return_value = mock_cl
        mock_print_cls.return_value.print_checklist.return_value = {"data": "formatted"}

        resp = client.post("/learning/checklists/1/print")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"
        app.config["message_broker_client"].send_message.assert_called_once()

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.get_checklist.return_value = None
        resp = client.post("/learning/checklists/999/print")
        assert resp.status_code == 404
