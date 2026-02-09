from dashboard.src.calendars.helpers import get_text_calendar


class TestGetTextCalendar:
    """Tests for the get_text_calendar helper."""

    def test_returns_string(self):
        """Test that get_text_calendar returns a string."""
        result = get_text_calendar()
        assert isinstance(result, str)

    def test_contains_august_2025(self):
        """Test that the calendar is for August 2025."""
        result = get_text_calendar()
        assert "August 2025" in result

    def test_contains_day_headers(self):
        """Test that the calendar contains day-of-week headers."""
        result = get_text_calendar()
        for day in ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]:
            assert day in result

    def test_contains_days_of_month(self):
        """Test that the calendar contains days 1-31."""
        result = get_text_calendar()
        assert " 1 " in result or result.endswith(" 1") or "1\n" in result
        assert "31" in result

    def test_starts_on_sunday(self):
        """Test that the calendar week starts on Sunday."""
        result = get_text_calendar()
        lines = result.strip().split("\n")
        header_line = lines[1]
        assert header_line.strip().startswith("Su")
