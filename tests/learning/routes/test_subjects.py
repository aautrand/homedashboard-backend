import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.learning.routes.subjects import subjects_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(app, mock_db):
    app.register_blueprint(subjects_bp, url_prefix="/learning")

    @app.before_request
    def inject_db():
        from flask import request

        request.db = mock_db

    return app.test_client()


class TestCreateSubject:

    @patch("dashboard.src.learning.routes.subjects.SubjectManager")
    def test_success(self, mock_cls, client):
        mock_sub = MagicMock()
        mock_sub.to_dict.return_value = {"id": 1, "name": "Math"}
        mock_cls.return_value.add_subject.return_value = mock_sub

        resp = client.post(
            "/learning/subjects",
            data=json.dumps({"name": "Math"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert resp.get_json()["name"] == "Math"

    def test_missing_name(self, client):
        resp = client.post(
            "/learning/subjects",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestGetSubjects:

    @patch("dashboard.src.learning.routes.subjects.SubjectManager")
    def test_all(self, mock_cls, client):
        mock_sub = MagicMock()
        mock_sub.to_dict.return_value = {"id": 1, "name": "Math"}
        mock_cls.return_value.get_all_subjects.return_value = [mock_sub]

        resp = client.get("/learning/subjects")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 1

    @patch("dashboard.src.learning.routes.subjects.SubjectManager")
    def test_study_active_filter(self, mock_cls, client):
        mock_cls.return_value.get_study_subjects.return_value = []
        resp = client.get("/learning/subjects?study_active=true")
        assert resp.status_code == 200
        mock_cls.return_value.get_study_subjects.assert_called_once()


class TestGetSubjectById:

    @patch("dashboard.src.learning.routes.subjects.SubjectManager")
    def test_found(self, mock_cls, client):
        mock_sub = MagicMock()
        mock_sub.to_dict.return_value = {"id": 1, "name": "Math"}
        # The route accesses subject_manager.db.get(Subject, id)
        mock_cls.return_value.db.get.return_value = mock_sub

        resp = client.get("/learning/subjects/1")
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.subjects.SubjectManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.db.get.return_value = None
        resp = client.get("/learning/subjects/999")
        assert resp.status_code == 404


class TestUpdateSubject:

    @patch("dashboard.src.learning.routes.subjects.SubjectManager")
    def test_success(self, mock_cls, client):
        mock_sub = MagicMock()
        mock_sub.to_dict.return_value = {"id": 1, "name": "Updated"}
        mock_cls.return_value.update_subject.return_value = mock_sub

        resp = client.put(
            "/learning/subjects/1",
            data=json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.subjects.SubjectManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.update_subject.return_value = None
        resp = client.put(
            "/learning/subjects/999",
            data=json.dumps({"name": "X"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_no_data(self, client):
        resp = client.put("/learning/subjects/1", content_type="application/json")
        assert resp.status_code == 400


class TestStudyEnableDisable:

    @patch("dashboard.src.learning.routes.subjects.SubjectManager")
    def test_enable(self, mock_cls, client):
        mock_sub = MagicMock()
        mock_sub.to_dict.return_value = {"id": 1, "study_active": True}
        mock_cls.return_value.update_subject.return_value = mock_sub

        resp = client.post("/learning/subjects/1/study/enable")
        assert resp.status_code == 200
        mock_cls.return_value.update_subject.assert_called_once_with(
            1, study_active=True
        )

    @patch("dashboard.src.learning.routes.subjects.SubjectManager")
    def test_disable(self, mock_cls, client):
        mock_sub = MagicMock()
        mock_sub.to_dict.return_value = {"id": 1, "study_active": False}
        mock_cls.return_value.update_subject.return_value = mock_sub

        resp = client.post("/learning/subjects/1/study/disable")
        assert resp.status_code == 200
        mock_cls.return_value.update_subject.assert_called_once_with(
            1, study_active=False
        )

    @patch("dashboard.src.learning.routes.subjects.SubjectManager")
    def test_enable_not_found(self, mock_cls, client):
        mock_cls.return_value.update_subject.return_value = None
        resp = client.post("/learning/subjects/999/study/enable")
        assert resp.status_code == 404


class TestGetTodaysStudies:

    @patch("dashboard.src.learning.routes.subjects.SubjectManager")
    def test_success(self, mock_cls, client):
        mock_sub = MagicMock()
        mock_sub.to_dict.return_value = {"id": 1, "name": "Math"}
        mock_cls.return_value.get_subjects_for_study_today.return_value = [mock_sub]

        resp = client.get("/learning/subjects/study/today")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 1
