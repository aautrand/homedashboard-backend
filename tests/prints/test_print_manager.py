import json
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from dashboard.src.prints.print_manager import PrintManager


class TestExtractWeather:

    def test_formats_weather(self):
        weather = MagicMock()
        weather.weather = [MagicMock(description="clear sky")]
        weather.main.temp = 20.0
        weather.daily_min_temp = 15.0
        weather.daily_max_temp = 25.0

        items = PrintManager.extract_weather(weather)
        assert len(items) == 4
        assert "20" in items[0]  # Current temp celsius
        assert "68" in items[0]  # Current temp fahrenheit
        assert "15" in items[1]  # Min celsius
        assert "25" in items[1]  # Max celsius
        assert "clear sky" in items[3]

    def test_multiple_conditions(self):
        weather = MagicMock()
        weather.weather = [
            MagicMock(description="clouds"),
            MagicMock(description="rain"),
        ]
        weather.main.temp = 10.0
        weather.daily_min_temp = 5.0
        weather.daily_max_temp = 15.0

        items = PrintManager.extract_weather(weather)
        assert "clouds, rain" in items[3]


class TestExtractBirthdays:

    def test_extracts_birthdays(self):
        events = [
            json.dumps({"summary": "Alice's Birthday", "start_time": "2025-10-02"}),
            json.dumps({"summary": "Meeting", "start_time": "2025-10-02"}),
        ]
        birthdays = PrintManager.extract_birthdays(events)
        assert birthdays == ["Alice"]
        assert len(events) == 1  # Birthday event removed

    def test_no_birthdays(self):
        events = [json.dumps({"summary": "Meeting", "start_time": "2025-10-02"})]
        birthdays = PrintManager.extract_birthdays(events)
        assert birthdays == []
        assert len(events) == 1


class TestExtractBirthdaysFromDB:

    def test_extracts_birthdays(self):
        bday_event = MagicMock()
        bday_event.summary = "Bob's Birthday"
        other_event = MagicMock()
        other_event.summary = "Meeting"

        birthdays, remaining = PrintManager.extract_birthdays_from_db(
            [bday_event, other_event]
        )
        assert birthdays == ["Bob"]
        assert remaining == [other_event]

    def test_no_birthdays(self):
        event = MagicMock()
        event.summary = "Meeting"
        birthdays, remaining = PrintManager.extract_birthdays_from_db([event])
        assert birthdays == []
        assert remaining == [event]


class TestExtractEventsFromDB:

    def test_categorizes_all_day_event(self):
        event = MagicMock()
        event.start_time = datetime(2025, 10, 2, 0, 0, 0)
        event.summary = "Holiday"

        from datetime import date

        today = date(2025, 10, 2)
        all_day, timed = PrintManager.extract_events_from_db([event], today)
        assert all_day == ["Holiday"]
        assert timed == []

    def test_categorizes_timed_event(self):
        event = MagicMock()
        event.start_time = datetime(2025, 10, 2, 14, 30, 0)
        event.summary = "Meeting"

        from datetime import date

        today = date(2025, 10, 2)
        all_day, timed = PrintManager.extract_events_from_db([event], today)
        assert all_day == []
        assert timed == [("14:30", "Meeting")]

    def test_skips_other_dates(self):
        event = MagicMock()
        event.start_time = datetime(2025, 10, 3, 10, 0, 0)
        event.summary = "Tomorrow"

        from datetime import date

        today = date(2025, 10, 2)
        all_day, timed = PrintManager.extract_events_from_db([event], today)
        assert all_day == []
        assert timed == []

    def test_sorts_timed_events(self):
        e1 = MagicMock()
        e1.start_time = datetime(2025, 10, 2, 16, 0)
        e1.summary = "Late"
        e2 = MagicMock()
        e2.start_time = datetime(2025, 10, 2, 9, 0)
        e2.summary = "Early"

        from datetime import date

        today = date(2025, 10, 2)
        _, timed = PrintManager.extract_events_from_db([e1, e2], today)
        assert timed[0] == ("09:00", "Early")
        assert timed[1] == ("16:00", "Late")


class TestPrintChecklist:

    def test_builds_receipt(self):
        checklist = MagicMock()
        checklist.title = "Shopping"
        checklist.items = ["Milk", "Eggs"]

        result = PrintManager.print_checklist(checklist)
        assert "title" in result
        assert " Shopping " in result


class TestPrintReminder:

    def test_builds_receipt(self):
        reminder = MagicMock()
        reminder.title = "Water plants"

        result = PrintManager.print_reminder(reminder)
        assert " Reminder " in result
        assert any("Water plants" in str(v) for v in result.values())


class TestPrintTodo:

    def test_builds_receipt(self):
        todo = MagicMock()
        todo.title = "Buy groceries"

        result = PrintManager.print_todo(todo)
        assert " To Do's " in result


class TestPrintEvent:

    def test_timed_event(self):
        event = MagicMock()
        event.start_time = datetime(2025, 10, 2, 14, 30)
        event.summary = "Meeting"

        result = PrintManager.print_event(event)
        assert " Upcoming Event " in result

    def test_all_day_event(self):
        event = MagicMock()
        event.start_time = datetime(2025, 10, 2, 0, 0)
        event.summary = "Holiday"

        result = PrintManager.print_event(event)
        assert " Upcoming Event " in result


class TestPrintText:

    def test_builds_receipt(self):
        result = PrintManager.print_text(["Line 1", "Line 2"])
        assert "title" in result
        assert result["title"] == ""


class TestBuildPopQuiz:

    def test_with_cards(self):
        card1 = MagicMock()
        card1.title = "What is 2+2?"
        card2 = MagicMock()
        card2.title = "Capital of France?"

        result = PrintManager.build_pop_quiz([card1, card2], quiz_id=42)
        assert " Pop Quiz " in result
        assert "#42" in result["title"]

    def test_without_quiz_id(self):
        card = MagicMock()
        card.title = "Question"
        result = PrintManager.build_pop_quiz([card])
        assert "#" not in result["title"]

    def test_empty_cards(self):
        result = PrintManager.build_pop_quiz([])
        assert "title" in result


class TestBuildPopQuizAnswers:

    def test_with_cards(self):
        card = MagicMock()
        card.title = "Question"
        card.content = "Answer"

        result = PrintManager.build_pop_quiz_answers([card])
        assert " Pop Quiz Answers " in result

    def test_empty_cards(self):
        result = PrintManager.build_pop_quiz_answers([])
        assert "title" in result
