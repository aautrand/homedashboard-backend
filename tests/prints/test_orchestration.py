import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.prints.orchestration import (
    print_pop_quiz,
    print_quiz_answers,
    reprint_quiz,
)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["message_broker_client"] = MagicMock()
    return app


class TestPrintPopQuiz:

    def test_no_cards_available(self, app):
        with app.app_context():
            mock_db = MagicMock()
            with patch("dashboard.src.prints.orchestration.CardManager") as mock_cm:
                mock_cm.return_value.get_non_grokked_cards.return_value = []
                result = print_pop_quiz(mock_db)
                assert result["status"] == "ok"
                assert result["quiz_id"] is None
                assert result["question_count"] == 0

    def test_with_cards(self, app):
        with app.app_context():
            mock_db = MagicMock()
            card1 = MagicMock()
            card1.title = "Q1"
            card1.content = "A1"
            card2 = MagicMock()
            card2.title = "Q2"
            card2.content = "A2"

            with patch("dashboard.src.prints.orchestration.CardManager") as mock_cm, \
                 patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm:
                mock_cm.return_value.get_non_grokked_cards.return_value = [card1, card2]
                mock_quiz = MagicMock()
                mock_quiz.id = 1
                mock_qm.return_value.create_quiz.return_value = mock_quiz

                result = print_pop_quiz(mock_db)
                assert result["status"] == "ok"
                assert result["quiz_id"] == 1
                assert result["question_count"] == 2
                # Should send quiz + answers
                rabbit = app.config["message_broker_client"]
                assert rabbit.send_message.call_count == 2

    def test_with_num_questions_limit(self, app):
        with app.app_context():
            mock_db = MagicMock()
            cards = [MagicMock(title=f"Q{i}", content=f"A{i}") for i in range(5)]

            with patch("dashboard.src.prints.orchestration.CardManager") as mock_cm, \
                 patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm:
                mock_cm.return_value.get_non_grokked_cards.return_value = cards
                mock_quiz = MagicMock()
                mock_quiz.id = 2
                mock_qm.return_value.create_quiz.return_value = mock_quiz

                result = print_pop_quiz(mock_db, num_questions=2)
                assert result["question_count"] == 2

    def test_without_answers(self, app):
        with app.app_context():
            mock_db = MagicMock()
            card = MagicMock(title="Q", content="A")

            with patch("dashboard.src.prints.orchestration.CardManager") as mock_cm, \
                 patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm:
                mock_cm.return_value.get_non_grokked_cards.return_value = [card]
                mock_quiz = MagicMock()
                mock_quiz.id = 3
                mock_qm.return_value.create_quiz.return_value = mock_quiz

                result = print_pop_quiz(mock_db, include_answers=False)
                assert result["status"] == "ok"
                # Should send quiz only, not answers
                rabbit = app.config["message_broker_client"]
                assert rabbit.send_message.call_count == 1


class TestReprintQuiz:

    def test_quiz_not_found(self, app):
        with app.app_context():
            mock_db = MagicMock()
            with patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm:
                mock_qm.return_value.get_quiz.return_value = None
                result = reprint_quiz(mock_db, quiz_id=99)
                assert result["status"] == "error"
                assert result["quiz_id"] == 99

    def test_quiz_no_questions(self, app):
        with app.app_context():
            mock_db = MagicMock()
            with patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm:
                mock_qm.return_value.get_quiz.return_value = MagicMock()
                mock_qm.return_value.get_quiz_questions.return_value = []
                result = reprint_quiz(mock_db, quiz_id=1)
                assert result["status"] == "ok"
                assert result["question_count"] == 0

    def test_success(self, app):
        with app.app_context():
            mock_db = MagicMock()
            mock_q = MagicMock()
            mock_q.card = MagicMock(title="Q1", content="A1")

            with patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm:
                mock_qm.return_value.get_quiz.return_value = MagicMock()
                mock_qm.return_value.get_quiz_questions.return_value = [mock_q]
                result = reprint_quiz(mock_db, quiz_id=1)
                assert result["status"] == "ok"
                assert result["question_count"] == 1

    def test_without_answers(self, app):
        with app.app_context():
            mock_db = MagicMock()
            mock_q = MagicMock()
            mock_q.card = MagicMock(title="Q1", content="A1")

            with patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm:
                mock_qm.return_value.get_quiz.return_value = MagicMock()
                mock_qm.return_value.get_quiz_questions.return_value = [mock_q]
                result = reprint_quiz(mock_db, quiz_id=1, include_answers=False)
                rabbit = app.config["message_broker_client"]
                assert rabbit.send_message.call_count == 1


class TestPrintQuizAnswers:

    def test_quiz_not_found(self, app):
        with app.app_context():
            mock_db = MagicMock()
            with patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm:
                mock_qm.return_value.get_quiz.return_value = None
                result = print_quiz_answers(mock_db, quiz_id=99)
                assert result["status"] == "error"

    def test_no_questions(self, app):
        with app.app_context():
            mock_db = MagicMock()
            with patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm:
                mock_qm.return_value.get_quiz.return_value = MagicMock()
                mock_qm.return_value.get_quiz_questions.return_value = []
                result = print_quiz_answers(mock_db, quiz_id=1)
                assert result["question_count"] == 0

    def test_success(self, app):
        with app.app_context():
            mock_db = MagicMock()
            mock_q = MagicMock()
            mock_q.card = MagicMock(title="Q1", content="A1")

            with patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm:
                mock_qm.return_value.get_quiz.return_value = MagicMock()
                mock_qm.return_value.get_quiz_questions.return_value = [mock_q]
                result = print_quiz_answers(mock_db, quiz_id=1)
                assert result["status"] == "ok"
                assert result["question_count"] == 1
