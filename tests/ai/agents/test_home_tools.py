import json
from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from dashboard.src.ai.agents.home_tools import build_home_tools


@pytest.fixture
def services():
    return MagicMock()


@pytest.fixture
def tools(services):
    return {tool.name: tool for tool in build_home_tools(services)}


def make(**fields):
    obj = MagicMock()
    for key, value in fields.items():
        setattr(obj, key, value)
    return obj


class TestToolSet:
    def test_exposes_expected_tools(self, tools):
        assert set(tools) == {
            "list_todos",
            "add_todo",
            "complete_todo",
            "get_calendar_events",
            "get_weather",
            "search_quotes",
            "add_quote",
            "pin_quote",
            "create_flashcard",
            "print_text",
        }

    def test_every_tool_has_a_description(self, tools):
        assert all(tool.description for tool in tools.values())


class TestTodoTools:
    def test_list_todos(self, tools, services):
        services.todos.get_active_todos.return_value = [
            make(id=1, title="Buy milk"),
            make(id=2, title="Call mom"),
        ]

        result = json.loads(tools["list_todos"].invoke({}))

        assert result == [
            {"id": 1, "title": "Buy milk"},
            {"id": 2, "title": "Call mom"},
        ]

    def test_add_todo(self, tools, services):
        services.todos.add_todo.return_value = make(id=3, title="Water plants")

        result = json.loads(tools["add_todo"].invoke({"title": "Water plants"}))

        services.todos.add_todo.assert_called_once_with(title="Water plants")
        assert result == {"id": 3, "title": "Water plants"}

    def test_complete_todo_does_not_print(self, tools, services):
        services.todos.complete_todo.return_value = make(id=1, title="Buy milk")

        result = json.loads(tools["complete_todo"].invoke({"todo_id": 1}))

        services.todos.complete_todo.assert_called_once_with(1)
        services.printer.assert_not_called()
        assert services.printer.method_calls == []
        assert result == {"id": 1, "title": "Buy milk", "done": True}

    def test_complete_todo_not_found(self, tools, services):
        services.todos.complete_todo.return_value = None

        assert tools["complete_todo"].invoke({"todo_id": 9}) == "No todo with ID 9."


class TestCalendarTool:
    def test_parses_iso_date(self, tools, services):
        services.calendar.get_synced_events_for_date.return_value = [
            make(
                summary="Dentist",
                calendar="Home",
                start_time=datetime(2026, 10, 7, 9, 0),
                end_time=datetime(2026, 10, 7, 10, 0),
            )
        ]

        result = json.loads(tools["get_calendar_events"].invoke({"day": "2026-10-07"}))

        services.calendar.get_synced_events_for_date.assert_called_once_with(
            date(2026, 10, 7)
        )
        assert result[0]["summary"] == "Dentist"
        assert result[0]["start"] == "2026-10-07 09:00:00"


class TestWeatherTool:
    def test_returns_weather_json(self, tools, services):
        services.weather.get_weather.return_value.to_json.return_value = '{"t": 1}'

        assert tools["get_weather"].invoke({}) == '{"t": 1}'


class TestQuoteTools:
    def test_search_quotes(self, tools, services):
        services.quotes.search_quotes.return_value = [
            make(id=4, text="Luck is...", author="Seneca", pinned=False)
        ]

        result = json.loads(tools["search_quotes"].invoke({"query": "seneca"}))

        services.quotes.search_quotes.assert_called_once_with("seneca")
        assert result == [
            {"id": 4, "text": "Luck is...", "author": "Seneca", "pinned": False}
        ]

    def test_add_quote_author_optional(self, tools, services):
        services.quotes.add_quote.return_value = make(id=5, text="Hi", author=None)

        tools["add_quote"].invoke({"text": "Hi"})

        services.quotes.add_quote.assert_called_once_with(text="Hi", author=None)

    def test_pin_quote(self, tools, services):
        services.quotes.pin_quote.return_value = make(id=4, text="Luck is...")

        result = json.loads(tools["pin_quote"].invoke({"quote_id": 4}))

        services.quotes.pin_quote.assert_called_once_with(4)
        assert result["pinned"] is True

    def test_pin_quote_not_found(self, tools, services):
        services.quotes.pin_quote.return_value = None

        assert tools["pin_quote"].invoke({"quote_id": 4}) == "No quote with ID 4."


class TestFlashcardAndPrintTools:
    def test_create_flashcard(self, tools, services):
        services.cards.add_card.return_value = make(id=7, title="What is ATP?")

        result = json.loads(
            tools["create_flashcard"].invoke(
                {"title": "What is ATP?", "content": "Cell energy currency"}
            )
        )

        services.cards.add_card.assert_called_once_with(
            title="What is ATP?", content="Cell energy currency"
        )
        assert result == {"id": 7, "title": "What is ATP?"}

    def test_print_text(self, tools, services):
        assert tools["print_text"].invoke({"text": "hello"}) == "Printed."

        services.printer.print_text.assert_called_once_with("hello")
