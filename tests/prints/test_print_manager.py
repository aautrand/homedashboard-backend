import json
from datetime import datetime
from unittest.mock import MagicMock

from dashboard.src.prints.print_manager import PrintManager
from dashboard.src.prints.receipts.formatter import RECEIPT_WIDTH


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
        assert " To Do " in result


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


class TestPrintVoiceResponse:

    def test_title_is_timestamp_and_body_is_reply(self):
        result = PrintManager.print_voice_response(
            "It's 12:18 PM.\nAnything else?", datetime(2026, 10, 6, 12, 18)
        )

        assert "Oct 06, 2026 12:18" in result["title"]
        body = json.dumps(result)
        assert "It's 12:18 PM." in body
        assert "Anything else?" in body
        assert "You asked" not in body


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


class TestExtractQuotes:

    @staticmethod
    def _quote(text, author=None):
        quote = MagicMock()
        quote.text = text
        quote.author = author
        return quote

    def test_no_quotes_returns_empty(self):
        assert PrintManager.extract_quotes(None, None) == []

    def test_random_quote_only(self):
        result = PrintManager.extract_quotes(self._quote("Be here now"), None)

        assert result == ["", '"Be here now"'.center(RECEIPT_WIDTH).rstrip(), ""]

    def test_pinned_quote_only(self):
        result = PrintManager.extract_quotes(None, self._quote("Slow is smooth"))

        # The pinned quote carries a wider margin than the random one.
        assert result == [
            "",
            "",
            '"Slow is smooth"'.center(RECEIPT_WIDTH).rstrip(),
            "",
            "",
        ]

    def test_includes_author_when_present(self):
        result = PrintManager.extract_quotes(
            self._quote("The obstacle is the way", author="Marcus Aurelius"), None
        )

        assert result == [
            "",
            '"The obstacle is the way"'.center(RECEIPT_WIDTH).rstrip(),
            "- Marcus Aurelius".center(RECEIPT_WIDTH).rstrip(),
            "",
        ]

    def test_random_prints_above_pinned(self):
        result = PrintManager.extract_quotes(
            self._quote("Random one"), self._quote("Pinned one")
        )
        stripped = [line.strip() for line in result]

        assert stripped.index('"Random one"') < stripped.index('"Pinned one"')

    def test_pinned_gets_wider_margin_than_random(self):
        result = PrintManager.extract_quotes(
            self._quote("Random one", author="Someone"),
            self._quote("Pinned one"),
        )
        stripped = [line.strip() for line in result]

        assert stripped == [
            "",
            '"Random one"',
            "- Someone",
            "",
            "",
            '"Pinned one"',
            "",
            "",
        ]

    def test_author_sits_outside_the_quote_marks(self):
        result = PrintManager.extract_quotes(
            self._quote("Be here now", author="Ram Dass"), None
        )
        stripped = [line.strip() for line in result if line.strip()]

        assert stripped == ['"Be here now"', "- Ram Dass"]

    def test_lines_are_centered(self):
        result = PrintManager.extract_quotes(self._quote("Short"), None)
        line = result[1]

        # Leading padding is half the slack; the trailing half is dropped.
        expected_pad = (RECEIPT_WIDTH - len('"Short"')) // 2
        assert line == " " * expected_pad + '"Short"'

    def test_long_quote_wraps_on_word_boundaries(self):
        text = (
            "The impediment to action advances action. "
            "What stands in the way becomes the way."
        )
        result = PrintManager.extract_quotes(self._quote(text), None)
        lines = [line.strip() for line in result if line.strip()]

        assert len(lines) > 1
        # Every word survives intact and in order, quote marks included.
        assert " ".join(lines) == f'"{text}"'
        assert all(len(line) <= RECEIPT_WIDTH for line in result)

    def test_no_line_exceeds_receipt_width(self):
        result = PrintManager.extract_quotes(
            self._quote("A rather long saying that will certainly need wrapping here"),
            self._quote("Another lengthy pinned saying that also needs to be wrapped"),
        )

        assert all(len(line) <= RECEIPT_WIDTH for line in result)

    def test_each_wrapped_line_is_centered(self):
        text = "A rather long saying that will certainly need wrapping right here"
        result = PrintManager.extract_quotes(self._quote(text), None)

        for line in result:
            if not line.strip():
                continue
            leading = len(line) - len(line.lstrip())
            trailing = RECEIPT_WIDTH - len(line)
            # Centred to within the odd-length remainder.
            assert abs(trailing - leading) <= 1


class TestQuoted:

    def test_adds_quote_marks(self):
        assert PrintManager.quoted("hello") == '"hello"'

    def test_strips_surrounding_whitespace(self):
        assert PrintManager.quoted("  hello  ") == '"hello"'

    def test_does_not_double_up_existing_marks(self):
        assert PrintManager.quoted('"hello"') == '"hello"'

    def test_leaves_curly_quotes_alone(self):
        assert PrintManager.quoted("\u201chello\u201d") == "\u201chello\u201d"

    def test_quotes_text_containing_inner_marks(self):
        assert PrintManager.quoted('say "hi" back') == '"say "hi" back"'


class TestCenterText:

    def test_centers_single_line(self):
        assert PrintManager.center_text("hi") == ["hi".center(RECEIPT_WIDTH).rstrip()]

    def test_empty_string_yields_blank_line(self):
        assert PrintManager.center_text("") == [""]

    def test_preserves_explicit_line_breaks(self):
        result = PrintManager.center_text("first\nsecond")

        assert [line.strip() for line in result] == ["first", "second"]

    def test_does_not_split_long_words(self):
        word = "x" * (RECEIPT_WIDTH + 10)
        result = PrintManager.center_text(word)

        assert result == [word]

    def test_respects_custom_width(self):
        result = PrintManager.center_text("one two three four five", width=10)

        assert all(len(line) <= 10 for line in result)
        assert " ".join(line.strip() for line in result) == "one two three four five"


class TestPrintIngredients:
    def test_checklist_with_plain_headers(self):
        from dashboard.src.prints.print_manager import PrintManager
        from dashboard.src.recipes.models import Ingredient, Recipe, Step

        recipe = Recipe(
            id=1,
            name="Lasagna",
            steps=[
                Step(
                    instruction="",
                    ingredients=[
                        Ingredient(food="For the sauce", is_header=True),
                        Ingredient(food="tomatoes", amount=800, unit="g"),
                    ],
                )
            ],
        )

        receipt = PrintManager.print_ingredients(recipe)

        assert receipt[" Lasagna "] == ["-- For the sauce --", "[ ] 800 g tomatoes"]
