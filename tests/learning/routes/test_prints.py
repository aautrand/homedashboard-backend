import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.learning.routes.prints import prints_bp


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
    app.register_blueprint(prints_bp, url_prefix="/learning")

    @app.before_request
    def inject_db():
        from flask import request
        request.db = mock_db

    return app.test_client()


class TestPrintPopQuiz:

    @patch("dashboard.src.learning.routes.prints.orchestration")
    def test_success(self, mock_orch, client):
        mock_orch.print_pop_quiz.return_value = {
            "status": "ok",
            "quiz_id": 1,
            "question_count": 5,
            "message": "Printed 5 questions",
        }
        resp = client.post(
            "/learning/print/pop-quiz",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        mock_orch.print_pop_quiz.assert_called_once()

    @patch("dashboard.src.learning.routes.prints.orchestration")
    def test_with_options(self, mock_orch, client):
        mock_orch.print_pop_quiz.return_value = {"status": "ok"}
        resp = client.post(
            "/learning/print/pop-quiz",
            data=json.dumps({"num_questions": 3, "include_answers": False}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        call_kwargs = mock_orch.print_pop_quiz.call_args
        assert call_kwargs.kwargs["num_questions"] == 3
        assert call_kwargs.kwargs["include_answers"] is False


class TestReprintQuiz:

    @patch("dashboard.src.learning.routes.prints.orchestration")
    def test_success(self, mock_orch, client):
        mock_orch.reprint_quiz.return_value = {
            "status": "ok",
            "quiz_id": 1,
            "question_count": 5,
            "message": "Reprinted quiz",
        }
        resp = client.post(
            "/learning/print/quiz/1",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.prints.orchestration")
    def test_with_options(self, mock_orch, client):
        mock_orch.reprint_quiz.return_value = {"status": "ok"}
        resp = client.post(
            "/learning/print/quiz/1",
            data=json.dumps({"include_answers": False, "randomize": False}),
            content_type="application/json",
        )
        call_kwargs = mock_orch.reprint_quiz.call_args
        assert call_kwargs.kwargs["include_answers"] is False
        assert call_kwargs.kwargs["randomize"] is False


class TestPrintQuizAnswers:

    @patch("dashboard.src.learning.routes.prints.orchestration")
    def test_success(self, mock_orch, client):
        mock_orch.print_quiz_answers.return_value = {"status": "ok"}
        resp = client.post("/learning/print/quiz/1/answers")
        assert resp.status_code == 200


class TestGetQuizzes:

    @patch("dashboard.src.learning.learning_manager.QuizManager")
    def test_success(self, mock_cls, client):
        mock_quiz = MagicMock()
        mock_quiz.id = 1
        mock_quiz.created_date = datetime(2025, 8, 15, 10, 0, 0)
        mock_quiz.questions = [MagicMock(), MagicMock()]
        mock_cls.return_value.get_all_quizzes.return_value = [mock_quiz]

        resp = client.get("/learning/quiz")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["question_count"] == 2
