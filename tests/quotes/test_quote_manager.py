from datetime import date
from unittest.mock import MagicMock

import pytest

from dashboard.src.quotes.models.quote import Quote
from dashboard.src.quotes.quote_manager import QuoteManager


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def manager(mock_db):
    return QuoteManager(mock_db)


def make_quote(
    quote_id=1, text="Be here now", author=None, times_shown=0, pinned=False
):
    quote = MagicMock()
    quote.id = quote_id
    quote.text = text
    quote.author = author
    quote.times_shown = times_shown
    quote.pinned = pinned
    quote.active = True
    return quote


def set_scalars(mock_db, results):
    """Point db.execute().scalars() at a fixed result list."""
    scalars = mock_db.execute.return_value.scalars.return_value
    scalars.all.return_value = results
    scalars.first.return_value = results[0] if results else None


class TestAddQuote:

    def test_adds_and_commits(self, manager, mock_db):
        quote = manager.add_quote("Slow is smooth", author="Anon")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert isinstance(quote, Quote)
        assert quote.text == "Slow is smooth"
        assert quote.author == "Anon"

    def test_defaults_to_active_without_author(self, manager):
        quote = manager.add_quote("Keep going")

        assert quote.author is None
        assert quote.active is True


class TestGetQuotes:

    def test_get_quote_by_id(self, manager, mock_db):
        expected = make_quote()
        mock_db.get.return_value = expected

        assert manager.get_quote(1) is expected
        mock_db.get.assert_called_once_with(Quote, 1)

    def test_get_all_quotes(self, manager, mock_db):
        set_scalars(mock_db, [make_quote(1), make_quote(2)])

        assert len(manager.get_all_quotes()) == 2

    def test_get_quotes_by_status(self, manager, mock_db):
        set_scalars(mock_db, [make_quote(1)])

        assert len(manager.get_quotes_by_status(True)) == 1


class TestUpdateAndDelete:

    def test_update_sets_fields(self, manager, mock_db):
        quote = make_quote()
        mock_db.get.return_value = quote

        manager.update_quote(1, text="New text")

        assert quote.text == "New text"
        mock_db.commit.assert_called_once()

    def test_update_ignores_unknown_fields(self, manager, mock_db):
        quote = Quote(text="Original")
        mock_db.get.return_value = quote

        manager.update_quote(1, nonsense="value")

        assert not hasattr(quote, "nonsense")

    def test_update_missing_returns_none(self, manager, mock_db):
        mock_db.get.return_value = None

        assert manager.update_quote(999, text="x") is None
        mock_db.commit.assert_not_called()

    def test_delete_removes(self, manager, mock_db):
        quote = make_quote()
        mock_db.get.return_value = quote

        assert manager.delete_quote(1) is quote
        mock_db.delete.assert_called_once_with(quote)
        mock_db.commit.assert_called_once()

    def test_delete_missing_returns_none(self, manager, mock_db):
        mock_db.get.return_value = None

        assert manager.delete_quote(999) is None
        mock_db.delete.assert_not_called()


class TestRandomSelection:

    def test_returns_none_when_pool_empty(self, manager, mock_db):
        set_scalars(mock_db, [])

        assert manager.get_random_quote() is None

    def test_picks_from_least_shown_only(self, manager, mock_db):
        never_shown = make_quote(1, "Fresh", times_shown=0)
        seen_often = make_quote(2, "Stale", times_shown=5)
        set_scalars(mock_db, [seen_often, never_shown])

        # Run enough times that a uniform pick over both would almost surely
        # surface the stale one at least once.
        picks = {manager.get_random_quote().id for _ in range(50)}

        assert picks == {1}

    def test_ties_in_least_shown_are_both_reachable(self, manager, mock_db):
        set_scalars(
            mock_db,
            [make_quote(1, times_shown=2), make_quote(2, times_shown=2)],
        )

        picks = {manager.get_random_quote().id for _ in range(50)}

        assert picks == {1, 2}

    def test_single_quote_pool_always_returns_it(self, manager, mock_db):
        set_scalars(mock_db, [make_quote(9, times_shown=3)])

        assert manager.get_random_quote().id == 9


class TestMarkShown:

    def test_increments_and_stamps_date(self, manager, mock_db):
        quote = make_quote(times_shown=2)
        mock_db.get.return_value = quote
        today = date(2026, 8, 21)

        manager.mark_quote_shown(1, today)

        assert quote.times_shown == 3
        assert quote.last_shown_date == today
        mock_db.commit.assert_called_once()

    def test_handles_null_counter(self, manager, mock_db):
        quote = make_quote()
        quote.times_shown = None
        mock_db.get.return_value = quote

        manager.mark_quote_shown(1, date(2026, 8, 21))

        assert quote.times_shown == 1

    def test_missing_quote_returns_none(self, manager, mock_db):
        mock_db.get.return_value = None

        assert manager.mark_quote_shown(999, date(2026, 8, 21)) is None
        mock_db.commit.assert_not_called()


class TestResetRotation:

    def test_clears_counters(self, manager, mock_db):
        quotes = [make_quote(1, times_shown=4), make_quote(2, times_shown=7)]
        set_scalars(mock_db, quotes)

        assert manager.reset_rotation() == 2
        assert all(q.times_shown == 0 for q in quotes)
        assert all(q.last_shown_date is None for q in quotes)
        mock_db.commit.assert_called_once()


class TestPinning:

    def test_get_pinned_returns_first(self, manager, mock_db):
        pinned = make_quote(3, pinned=True)
        set_scalars(mock_db, [pinned])

        assert manager.get_pinned_quote() is pinned

    def test_get_pinned_returns_none_when_unset(self, manager, mock_db):
        set_scalars(mock_db, [])

        assert manager.get_pinned_quote() is None

    def test_pin_sets_flag_and_date(self, manager, mock_db):
        target = make_quote(5, pinned=False)
        mock_db.get.return_value = target
        set_scalars(mock_db, [])

        result = manager.pin_quote(5, pinned_date=date(2026, 8, 21))

        assert result is target
        assert target.pinned is True
        assert target.pinned_date == date(2026, 8, 21)

    def test_pin_unpins_previous(self, manager, mock_db):
        previous = make_quote(1, pinned=True)
        target = make_quote(2, pinned=False)
        mock_db.get.return_value = target
        set_scalars(mock_db, [previous])

        manager.pin_quote(2)

        assert previous.pinned is False
        assert previous.pinned_date is None
        assert target.pinned is True

    def test_pin_missing_quote_returns_none(self, manager, mock_db):
        mock_db.get.return_value = None

        assert manager.pin_quote(999) is None
        mock_db.commit.assert_not_called()

    def test_unpin_clears_current(self, manager, mock_db):
        pinned = make_quote(4, pinned=True)
        set_scalars(mock_db, [pinned])

        result = manager.unpin_quote()

        assert result is pinned
        assert pinned.pinned is False
        mock_db.commit.assert_called_once()

    def test_unpin_with_nothing_pinned(self, manager, mock_db):
        set_scalars(mock_db, [])

        assert manager.unpin_quote() is None
        mock_db.commit.assert_not_called()


class TestCyclePinned:

    def test_pins_a_candidate(self, manager, mock_db):
        candidate = make_quote(2, pinned=False)
        # get_pinned_quote() then the candidate query, then _clear_pins().
        set_scalars(mock_db, [candidate])

        result = manager.cycle_pinned_quote(pinned_date=date(2026, 8, 21))

        assert result is candidate
        assert candidate.pinned is True
        assert candidate.pinned_date == date(2026, 8, 21)

    def test_keeps_current_when_no_other_candidates(self, manager, mock_db):
        current = make_quote(1, pinned=True)
        scalars = mock_db.execute.return_value.scalars.return_value
        scalars.first.return_value = current
        scalars.all.return_value = []

        result = manager.cycle_pinned_quote()

        assert result is current
        assert current.pinned is True

    def test_returns_none_when_pool_is_empty(self, manager, mock_db):
        set_scalars(mock_db, [])

        assert manager.cycle_pinned_quote() is None


class TestSearchQuotes:
    def test_returns_matches(self, manager, mock_db):
        quote = make_quote(text="Waste no more time", author="Marcus Aurelius")
        set_scalars(mock_db, [quote])

        assert manager.search_quotes("marcus") == [quote]

    def test_matches_text_or_author_ignoring_case(self, manager, mock_db):
        set_scalars(mock_db, [])

        manager.search_quotes("seneca")

        sql = str(
            mock_db.execute.call_args[0][0].compile(
                compile_kwargs={"literal_binds": True}
            )
        ).lower()
        assert "lower(quotes.text) like lower('%seneca%')" in sql
        assert "lower(quotes.author) like lower('%seneca%')" in sql
