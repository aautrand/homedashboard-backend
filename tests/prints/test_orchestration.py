import json
from contextlib import ExitStack
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.prints.orchestration import (
    print_pop_quiz,
    print_quiz_answers,
    print_tasks,
    reprint_quiz,
)
from dashboard.src.prints.receipts.formatter import RECEIPT_WIDTH


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["message_broker_client"] = MagicMock()
    return app


def _make_print_tasks_patches(
    active_reminders=None,
    active_todos=None,
    routine_tasks=None,
    db_events=None,
    non_grokked_cards=None,
    study_subjects=None,
    random_quote=None,
    pinned_quote=None,
):
    """Return a dict of patch targets with sensible defaults for print_tasks()."""
    reminder = MagicMock()
    reminder.id = 1
    reminder.title = "Drink water"

    todo = MagicMock()
    todo.id = 1
    todo.title = "Buy groceries"

    return {
        "dashboard.src.prints.orchestration.get_weather_client": MagicMock(
            return_value=MagicMock(
                get_current_weather=MagicMock(return_value=MagicMock()),
                get_forecast_weather=MagicMock(return_value=MagicMock()),
            )
        ),
        "dashboard.src.prints.orchestration.OpenWeather": MagicMock(
            from_current_and_forecast=MagicMock(
                return_value=MagicMock(
                    weather=[MagicMock(description="clear")],
                    main=MagicMock(temp=20.0),
                    daily_min_temp=15.0,
                    daily_max_temp=25.0,
                )
            )
        ),
        "dashboard.src.prints.orchestration.CalendarEventManager": MagicMock(
            return_value=MagicMock(
                sync_events=MagicMock(return_value={}),
                get_events_for_date=MagicMock(return_value=db_events or []),
            )
        ),
        "dashboard.src.prints.orchestration.RoutineTaskManager": MagicMock(
            return_value=MagicMock(
                get_tasks_for_date=MagicMock(return_value=routine_tasks or []),
            )
        ),
        "dashboard.src.prints.orchestration.ReminderManager": MagicMock(
            return_value=MagicMock(
                get_active_reminders=MagicMock(
                    return_value=(
                        active_reminders if active_reminders is not None else [reminder]
                    )
                ),
            )
        ),
        "dashboard.src.prints.orchestration.TodoManager": MagicMock(
            return_value=MagicMock(
                get_active_todos=MagicMock(
                    return_value=active_todos if active_todos is not None else [todo]
                ),
            )
        ),
        "dashboard.src.prints.orchestration.SubjectManager": MagicMock(
            return_value=MagicMock(
                get_subjects_for_study_today=MagicMock(
                    return_value=study_subjects or []
                ),
            )
        ),
        "dashboard.src.prints.orchestration.QuoteManager": MagicMock(
            return_value=MagicMock(
                get_pinned_quote=MagicMock(return_value=pinned_quote),
                get_random_quote=MagicMock(return_value=random_quote),
            )
        ),
        "dashboard.src.prints.orchestration.CardManager": MagicMock(
            return_value=MagicMock(
                get_non_grokked_cards=MagicMock(return_value=non_grokked_cards or []),
            )
        ),
        "dashboard.src.prints.print_manager.PrintManager.extract_weather": MagicMock(
            return_value=["20C / 68F", "Low: 15C", "High: 25C", "clear"]
        ),
        "dashboard.src.prints.print_manager.PrintManager.extract_birthdays_from_db": MagicMock(
            return_value=([], [])
        ),
        "dashboard.src.prints.print_manager.PrintManager.extract_events_from_db": MagicMock(
            return_value=([], [])
        ),
    }


@pytest.fixture
def print_tasks_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["LAT_LONG"] = "40.7128,-74.0060"
    app.config["MAIN_CALENDAR"] = "Home"
    return app


class TestPrintTasks:

    def _run(self, app, patches):
        with app.app_context(), app.test_request_context():
            from flask import request as flask_request

            flask_request.db = MagicMock()
            with ExitStack() as stack:
                for target, mock_val in patches.items():
                    stack.enter_context(patch(target, mock_val))
                return print_tasks()

    def test_returns_dict(self, print_tasks_app):
        patches = _make_print_tasks_patches()
        result = self._run(print_tasks_app, patches)
        assert isinstance(result, dict)

    def test_includes_reminders_section(self, print_tasks_app):
        reminder = MagicMock()
        reminder.id = 1
        reminder.title = "Take vitamins"
        patches = _make_print_tasks_patches(active_reminders=[reminder])
        result = self._run(print_tasks_app, patches)
        result_str = json.dumps(result)
        assert "Reminders" in result_str
        assert "Take vitamins" in result_str

    def test_includes_todos_section(self, print_tasks_app):
        todo = MagicMock()
        todo.id = 2
        todo.title = "Call dentist"
        patches = _make_print_tasks_patches(active_todos=[todo])
        result = self._run(print_tasks_app, patches)
        result_str = json.dumps(result)
        assert "To Do" in result_str
        assert "Call dentist" in result_str

    def test_reminders_and_todos_are_separate(self, print_tasks_app):
        reminder = MagicMock()
        reminder.id = 1
        reminder.title = "Water plants"
        todo = MagicMock()
        todo.id = 2
        todo.title = "Buy groceries"
        patches = _make_print_tasks_patches(
            active_reminders=[reminder], active_todos=[todo]
        )
        result = self._run(print_tasks_app, patches)
        result_str = json.dumps(result)
        assert "Water plants" in result_str
        assert "Buy groceries" in result_str
        assert "Reminders" in result_str
        assert "To Do" in result_str

    def _make_quote(self, quote_id=1, text="Be here now", author=None):
        quote = MagicMock()
        quote.id = quote_id
        quote.text = text
        quote.author = author
        return quote

    def test_includes_quotes_at_top(self, print_tasks_app):
        patches = _make_print_tasks_patches(
            random_quote=self._make_quote(1, "The obstacle is the way", "Aurelius"),
            pinned_quote=self._make_quote(2, "Slow is smooth"),
        )
        result = self._run(print_tasks_app, patches)

        keys = list(result.keys())
        assert keys[0] == "title"
        # The quote section is untitled and must sit directly under the date.
        assert keys[1] == ""
        stripped = [line.strip() for line in result[""]]
        assert '"The obstacle is the way"' in stripped
        assert "- Aurelius" in stripped
        assert '"Slow is smooth"' in stripped

    def test_quotes_are_centered(self, print_tasks_app):
        patches = _make_print_tasks_patches(random_quote=self._make_quote(1, "Short"))
        result = self._run(print_tasks_app, patches)

        expected_pad = (RECEIPT_WIDTH - len('"Short"')) // 2
        assert " " * expected_pad + '"Short"' in result[""]

    def test_quotes_padded_with_blank_lines(self, print_tasks_app):
        patches = _make_print_tasks_patches(random_quote=self._make_quote())
        result = self._run(print_tasks_app, patches)

        assert result[""][0] == ""
        assert result[""][-1] == ""

    def test_no_quote_section_when_pool_empty(self, print_tasks_app):
        patches = _make_print_tasks_patches()
        result = self._run(print_tasks_app, patches)

        assert "" not in result

    def test_marks_random_quote_shown(self, print_tasks_app):
        patches = _make_print_tasks_patches(random_quote=self._make_quote(4))
        self._run(print_tasks_app, patches)

        quote_mgr = patches[
            "dashboard.src.prints.orchestration.QuoteManager"
        ].return_value
        quote_mgr.mark_quote_shown.assert_called_once_with(4, date.today())

    def test_pinned_quote_does_not_advance_rotation(self, print_tasks_app):
        patches = _make_print_tasks_patches(pinned_quote=self._make_quote(9))
        self._run(print_tasks_app, patches)

        quote_mgr = patches[
            "dashboard.src.prints.orchestration.QuoteManager"
        ].return_value
        quote_mgr.mark_quote_shown.assert_not_called()

    def test_marks_reminders_shown(self, print_tasks_app):
        reminder = MagicMock()
        reminder.id = 7
        reminder.title = "Check mail"
        patches = _make_print_tasks_patches(active_reminders=[reminder])
        with print_tasks_app.app_context(), print_tasks_app.test_request_context():
            from flask import request as flask_request

            flask_request.db = MagicMock()
            with ExitStack() as stack:
                for target, mock_val in patches.items():
                    stack.enter_context(patch(target, mock_val))
                print_tasks()
                reminder_mgr = patches[
                    "dashboard.src.prints.orchestration.ReminderManager"
                ].return_value
                reminder_mgr.mark_reminder_shown.assert_called_once_with(
                    7, date.today()
                )

    def test_marks_todos_shown(self, print_tasks_app):
        todo = MagicMock()
        todo.id = 9
        todo.title = "Reply to emails"
        patches = _make_print_tasks_patches(active_todos=[todo])
        with print_tasks_app.app_context(), print_tasks_app.test_request_context():
            from flask import request as flask_request

            flask_request.db = MagicMock()
            with ExitStack() as stack:
                for target, mock_val in patches.items():
                    stack.enter_context(patch(target, mock_val))
                print_tasks()
                todo_mgr = patches[
                    "dashboard.src.prints.orchestration.TodoManager"
                ].return_value
                todo_mgr.mark_todo_shown.assert_called_once_with(9, date.today())

    def test_no_reminders_skips_section(self, print_tasks_app):
        patches = _make_print_tasks_patches(active_reminders=[])
        result = self._run(print_tasks_app, patches)
        result_str = json.dumps(result)
        assert "Reminders" not in result_str

    def test_no_todos_skips_section(self, print_tasks_app):
        patches = _make_print_tasks_patches(active_todos=[])
        result = self._run(print_tasks_app, patches)
        result_str = json.dumps(result)
        assert "To Do" not in result_str


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

            with (
                patch("dashboard.src.prints.orchestration.CardManager") as mock_cm,
                patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm,
            ):
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

            with (
                patch("dashboard.src.prints.orchestration.CardManager") as mock_cm,
                patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm,
            ):
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

            with (
                patch("dashboard.src.prints.orchestration.CardManager") as mock_cm,
                patch("dashboard.src.prints.orchestration.QuizManager") as mock_qm,
            ):
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
                reprint_quiz(mock_db, quiz_id=1, include_answers=False)
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
