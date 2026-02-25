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


def make_mock_note(note_id=1, checklist_id=1, content="Some note", position=0):
    note = MagicMock()
    note.to_dict.return_value = {
        "id": note_id,
        "checklist_id": checklist_id,
        "content": content,
        "position": position,
    }
    return note


class TestCreateChecklistNote:

    @patch("dashboard.src.learning.routes.checklists.ChecklistNoteManager")
    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_success(self, mock_cl_cls, mock_note_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = MagicMock()
        mock_note_cls.return_value.add_note.return_value = make_mock_note()

        resp = client.post(
            "/learning/checklists/1/notes",
            data=json.dumps({"content": "Some note"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert resp.get_json()["content"] == "Some note"

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_checklist_not_found(self, mock_cl_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = None

        resp = client.post(
            "/learning/checklists/999/notes",
            data=json.dumps({"content": "Some note"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_missing_content(self, mock_cl_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = MagicMock()

        resp = client.post(
            "/learning/checklists/1/notes",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestGetChecklistNotes:

    @patch("dashboard.src.learning.routes.checklists.ChecklistNoteManager")
    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_success(self, mock_cl_cls, mock_note_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = MagicMock()
        mock_note_cls.return_value.get_notes_for_checklist.return_value = [
            make_mock_note(1), make_mock_note(2)
        ]

        resp = client.get("/learning/checklists/1/notes")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 2

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_checklist_not_found(self, mock_cl_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = None

        resp = client.get("/learning/checklists/999/notes")
        assert resp.status_code == 404


class TestUpdateChecklistNote:

    @patch("dashboard.src.learning.routes.checklists.ChecklistNoteManager")
    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_success(self, mock_cl_cls, mock_note_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = MagicMock()
        mock_note_cls.return_value.update_note.return_value = make_mock_note(content="Updated")

        resp = client.put(
            "/learning/checklists/1/notes/1",
            data=json.dumps({"content": "Updated"}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_checklist_not_found(self, mock_cl_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = None

        resp = client.put(
            "/learning/checklists/999/notes/1",
            data=json.dumps({"content": "X"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    @patch("dashboard.src.learning.routes.checklists.ChecklistNoteManager")
    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_note_not_found(self, mock_cl_cls, mock_note_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = MagicMock()
        mock_note_cls.return_value.update_note.return_value = None

        resp = client.put(
            "/learning/checklists/1/notes/999",
            data=json.dumps({"content": "X"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_no_data(self, mock_cl_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = MagicMock()

        resp = client.put(
            "/learning/checklists/1/notes/1",
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestReorderChecklistNotes:

    @patch("dashboard.src.learning.routes.checklists.ChecklistNoteManager")
    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_success(self, mock_cl_cls, mock_note_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = MagicMock()
        mock_note_cls.return_value.get_notes_for_checklist.return_value = [
            make_mock_note(3, position=0),
            make_mock_note(1, position=1),
            make_mock_note(2, position=2),
        ]

        resp = client.put(
            "/learning/checklists/1/notes/reorder",
            data=json.dumps({"order": [3, 1, 2]}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert len(resp.get_json()) == 3
        mock_note_cls.return_value.reorder_notes.assert_called_once_with(1, [3, 1, 2])

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_checklist_not_found(self, mock_cl_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = None

        resp = client.put(
            "/learning/checklists/999/notes/reorder",
            data=json.dumps({"order": [1, 2]}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_missing_order(self, mock_cl_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = MagicMock()

        resp = client.put(
            "/learning/checklists/1/notes/reorder",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_invalid_order_not_list(self, mock_cl_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = MagicMock()

        resp = client.put(
            "/learning/checklists/1/notes/reorder",
            data=json.dumps({"order": "bad"}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestDeleteChecklistNote:

    @patch("dashboard.src.learning.routes.checklists.ChecklistNoteManager")
    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_success(self, mock_cl_cls, mock_note_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = MagicMock()
        mock_note_cls.return_value.delete_note.return_value = make_mock_note()

        resp = client.delete("/learning/checklists/1/notes/1")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Note deleted successfully"

    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_checklist_not_found(self, mock_cl_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = None

        resp = client.delete("/learning/checklists/999/notes/1")
        assert resp.status_code == 404

    @patch("dashboard.src.learning.routes.checklists.ChecklistNoteManager")
    @patch("dashboard.src.learning.routes.checklists.ChecklistManager")
    def test_note_not_found(self, mock_cl_cls, mock_note_cls, client):
        mock_cl_cls.return_value.get_checklist.return_value = MagicMock()
        mock_note_cls.return_value.delete_note.return_value = None

        resp = client.delete("/learning/checklists/1/notes/999")
        assert resp.status_code == 404