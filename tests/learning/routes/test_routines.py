import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.learning.routes.routines import routines_bp


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
    app.register_blueprint(routines_bp, url_prefix="/learning")

    @app.before_request
    def inject_db():
        from flask import request

        request.db = mock_db

    return app.test_client()


class TestCreateRoutine:

    @patch("dashboard.src.learning.routes.routines.RoutineTaskManager")
    def test_success_with_pattern(self, mock_cls, client):
        mock_rt = MagicMock()
        mock_rt.to_dict.return_value = {"id": 1, "title": "Workout"}
        mock_cls.return_value.add_routine_task.return_value = mock_rt

        resp = client.post(
            "/learning/routines",
            data=json.dumps({"title": "Workout", "schedule_pattern": "* * *"}),
            content_type="application/json",
        )
        assert resp.status_code == 201

    @patch("dashboard.src.learning.routes.routines.RoutineTaskManager")
    def test_success_with_interval(self, mock_cls, client):
        mock_rt = MagicMock()
        mock_rt.to_dict.return_value = {"id": 1, "title": "Review"}
        mock_cls.return_value.add_routine_task.return_value = mock_rt

        resp = client.post(
            "/learning/routines",
            data=json.dumps({"title": "Review", "interval_days": 3}),
            content_type="application/json",
        )
        assert resp.status_code == 201

    def test_missing_title(self, client):
        resp = client.post(
            "/learning/routines",
            data=json.dumps({"schedule_pattern": "* * *"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_no_schedule_type(self, client):
        resp = client.post(
            "/learning/routines",
            data=json.dumps({"title": "Task"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "schedule_pattern" in resp.get_json()["error"]


class TestGetRoutines:

    @patch("dashboard.src.learning.routes.routines.RoutineTaskManager")
    def test_all(self, mock_cls, client):
        mock_rt = MagicMock()
        mock_rt.to_dict.return_value = {"id": 1}
        mock_cls.return_value.get_all_routine_tasks.return_value = [mock_rt]

        resp = client.get("/learning/routines")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 1


class TestGetRoutine:

    @patch("dashboard.src.learning.routes.routines.RoutineTaskManager")
    def test_found(self, mock_cls, client):
        mock_rt = MagicMock()
        mock_rt.to_dict.return_value = {"id": 1}
        mock_cls.return_value.get_routine_task.return_value = mock_rt

        resp = client.get("/learning/routines/1")
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.routines.RoutineTaskManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.get_routine_task.return_value = None
        resp = client.get("/learning/routines/999")
        assert resp.status_code == 404


class TestUpdateRoutine:

    @patch("dashboard.src.learning.routes.routines.RoutineTaskManager")
    def test_success(self, mock_cls, client):
        mock_rt = MagicMock()
        mock_rt.to_dict.return_value = {"id": 1, "title": "Updated"}
        mock_cls.return_value.update_routine_task.return_value = mock_rt

        resp = client.put(
            "/learning/routines/1",
            data=json.dumps({"title": "Updated"}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.routines.RoutineTaskManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.update_routine_task.return_value = None
        resp = client.put(
            "/learning/routines/999",
            data=json.dumps({"title": "X"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_no_data(self, client):
        resp = client.put("/learning/routines/1", content_type="application/json")
        assert resp.status_code == 400


class TestDeleteRoutine:

    @patch("dashboard.src.learning.routes.routines.RoutineTaskManager")
    def test_success(self, mock_cls, client):
        mock_cls.return_value.delete_routine_task.return_value = MagicMock()
        resp = client.delete("/learning/routines/1")
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.routines.RoutineTaskManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.delete_routine_task.return_value = None
        resp = client.delete("/learning/routines/999")
        assert resp.status_code == 404


class TestGetTodaysRoutines:

    @patch("dashboard.src.learning.routes.routines.RoutineTaskManager")
    def test_success(self, mock_cls, client):
        mock_rt = MagicMock()
        mock_rt.to_dict.return_value = {"id": 1}
        mock_cls.return_value.get_tasks_for_date.return_value = [mock_rt]

        resp = client.get("/learning/routines/today")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 1
