import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.learning.routes.quizzes import quizzes_bp


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
    app.register_blueprint(quizzes_bp, url_prefix="/learning")

    @app.before_request
    def inject_db():
        from flask import request

        request.db = mock_db

    return app.test_client()


def _make_mock_question(id=1, quiz_id=1):
    q = MagicMock()
    q.id = id
    q.quiz_id = quiz_id
    return q


def _make_mock_answer(id=1, quiz_question_id=1, score=2):
    a = MagicMock()
    a.id = id
    a.quiz_question_id = quiz_question_id
    a.score = score
    a.score_label = "correct"
    a.created_date = datetime(2025, 8, 15, 10, 0, 0)
    return a


class TestRecordAnswer:

    @patch("dashboard.src.learning.routes.quizzes.QuizManager")
    def test_success(self, mock_cls, client):
        mock_q = _make_mock_question(id=10)
        mock_cls.return_value.get_quiz_questions.return_value = [mock_q]
        mock_answer = _make_mock_answer()
        mock_cls.return_value.record_answer.return_value = mock_answer

        resp = client.post(
            "/learning/quiz/1/question/10/answer",
            data=json.dumps({"score": 2}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["score"] == 2

    @patch("dashboard.src.learning.routes.quizzes.QuizManager")
    def test_question_not_in_quiz(self, mock_cls, client):
        mock_cls.return_value.get_quiz_questions.return_value = [
            _make_mock_question(id=99)
        ]

        resp = client.post(
            "/learning/quiz/1/question/10/answer",
            data=json.dumps({"score": 2}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_missing_score(self, client):
        resp = client.post(
            "/learning/quiz/1/question/1/answer",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_invalid_score(self, client):
        resp = client.post(
            "/learning/quiz/1/question/1/answer",
            data=json.dumps({"score": 5}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestRecordAnswersBulk:

    @patch("dashboard.src.learning.routes.quizzes.QuizManager")
    def test_success(self, mock_cls, client):
        q1 = _make_mock_question(id=1)
        q2 = _make_mock_question(id=2)
        mock_cls.return_value.get_quiz_questions.return_value = [q1, q2]
        mock_cls.return_value.record_answer.return_value = _make_mock_answer()

        resp = client.post(
            "/learning/quiz/1/answers",
            data=json.dumps(
                {
                    "answers": [
                        {"question_id": 1, "score": 2},
                        {"question_id": 2, "score": 0},
                    ]
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["answers_recorded"] == 2

    def test_missing_answers(self, client):
        resp = client.post(
            "/learning/quiz/1/answers",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_answers_not_a_list(self, client):
        resp = client.post(
            "/learning/quiz/1/answers",
            data=json.dumps({"answers": "not-a-list"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    @patch("dashboard.src.learning.routes.quizzes.QuizManager")
    def test_no_questions(self, mock_cls, client):
        mock_cls.return_value.get_quiz_questions.return_value = []
        resp = client.post(
            "/learning/quiz/1/answers",
            data=json.dumps({"answers": [{"question_id": 1, "score": 2}]}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    @patch("dashboard.src.learning.routes.quizzes.QuizManager")
    def test_question_not_in_quiz(self, mock_cls, client):
        mock_cls.return_value.get_quiz_questions.return_value = [
            _make_mock_question(id=99)
        ]
        resp = client.post(
            "/learning/quiz/1/answers",
            data=json.dumps({"answers": [{"question_id": 1, "score": 2}]}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    @patch("dashboard.src.learning.routes.quizzes.QuizManager")
    def test_invalid_score_in_bulk(self, mock_cls, client):
        q = _make_mock_question(id=1)
        mock_cls.return_value.get_quiz_questions.return_value = [q]
        resp = client.post(
            "/learning/quiz/1/answers",
            data=json.dumps({"answers": [{"question_id": 1, "score": 9}]}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    @patch("dashboard.src.learning.routes.quizzes.QuizManager")
    def test_missing_fields_in_answer(self, mock_cls, client):
        q = _make_mock_question(id=1)
        mock_cls.return_value.get_quiz_questions.return_value = [q]
        resp = client.post(
            "/learning/quiz/1/answers",
            data=json.dumps({"answers": [{"question_id": 1}]}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestGetQuiz:

    @patch("dashboard.src.learning.routes.quizzes.QuizManager")
    def test_found(self, mock_cls, client):
        mock_quiz = MagicMock()
        mock_quiz.id = 1
        mock_quiz.created_date = datetime(2025, 8, 15)

        mock_card = MagicMock()
        mock_card.id = 10
        mock_card.title = "Card Title"
        mock_card.content = "Card Content"

        mock_answer = MagicMock()
        mock_answer.id = 100
        mock_answer.score = 2
        mock_answer.score_label = "correct"
        mock_answer.created_date = datetime(2025, 8, 15, 10, 0, 0)

        mock_q = MagicMock()
        mock_q.id = 5
        mock_q.position = 0
        mock_q.card = mock_card
        mock_q.quiz = mock_quiz
        mock_q.answers = [mock_answer]

        mock_cls.return_value.get_quiz_questions.return_value = [mock_q]

        resp = client.get("/learning/quiz/1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["id"] == 1
        assert len(data["questions"]) == 1
        assert data["questions"][0]["card"]["title"] == "Card Title"

    @patch("dashboard.src.learning.routes.quizzes.QuizManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.get_quiz_questions.return_value = []
        resp = client.get("/learning/quiz/999")
        assert resp.status_code == 404
