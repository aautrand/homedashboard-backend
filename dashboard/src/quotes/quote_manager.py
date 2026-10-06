import random
from datetime import date
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from dashboard.src.quotes.models.quote import Quote


class QuoteManager:
    """Manages the pool of quotes printed at the top of the daily receipt.

    Two quotes are printed each day and both come from this single pool:
    one drawn at random from the least-shown quotes, and one "pinned" quote
    that stays put until it is explicitly cycled. The pinned quote is excluded
    from the random draw so the same text never prints twice in one receipt.
    """

    def __init__(self, db: Session):
        self.db = db

    def add_quote(self, text: str, author: str = None, active: bool = True) -> Quote:
        """Add a new quote to the pool."""
        quote = Quote(text=text, author=author, active=active)
        self.db.add(quote)
        self.db.commit()
        return quote

    def get_quote(self, quote_id: int) -> Optional[Quote]:
        """Get a specific quote by ID."""
        return self.db.get(Quote, quote_id)

    def get_all_quotes(self) -> list[Quote]:
        """Get every quote, newest first."""
        stmt = select(Quote).order_by(Quote.created_date.desc())
        return list(self.db.execute(stmt).scalars().all())

    def get_quotes_by_status(self, active: bool) -> list[Quote]:
        """Get quotes filtered by active status, newest first."""
        stmt = (
            select(Quote)
            .where(Quote.active == active)
            .order_by(Quote.created_date.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def search_quotes(self, query: str) -> list[Quote]:
        """Find quotes whose text or author contains `query`, ignoring case."""
        pattern = f"%{query}%"
        stmt = (
            select(Quote)
            .where(or_(Quote.text.ilike(pattern), Quote.author.ilike(pattern)))
            .order_by(Quote.created_date.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_quote(self, quote_id: int, **kwargs) -> Optional[Quote]:
        """Update a quote's fields."""
        quote = self.db.get(Quote, quote_id)
        if quote:
            for key, value in kwargs.items():
                if hasattr(quote, key):
                    setattr(quote, key, value)
            self.db.commit()
        return quote

    def delete_quote(self, quote_id: int) -> Optional[Quote]:
        """Delete a quote."""
        quote = self.db.get(Quote, quote_id)
        if quote:
            self.db.delete(quote)
            self.db.commit()
        return quote

    def get_random_quote(self) -> Optional[Quote]:
        """Pick a random quote that has been shown the fewest times.

        Drawing from the least-shown group means the whole pool is exhausted
        before anything repeats, while the pick within that group stays random.
        The pinned quote is skipped since it prints on its own line anyway.
        """
        stmt = select(Quote).where(Quote.active, Quote.pinned.is_(False))
        candidates = list(self.db.execute(stmt).scalars().all())

        if not candidates:
            return None

        fewest = min(quote.times_shown for quote in candidates)
        # Picks which quote to print; unpredictability is not a security property.
        return random.choice(  # nosec B311
            [quote for quote in candidates if quote.times_shown == fewest]
        )

    def mark_quote_shown(self, quote_id: int, shown_date: date) -> Optional[Quote]:
        """Record that a quote was printed on a specific date."""
        quote = self.db.get(Quote, quote_id)
        if quote:
            quote.last_shown_date = shown_date
            quote.times_shown = (quote.times_shown or 0) + 1
            self.db.commit()
        return quote

    def reset_rotation(self) -> int:
        """Clear the shown history so every quote is due again.

        Returns the number of quotes reset.
        """
        stmt = select(Quote)
        quotes = list(self.db.execute(stmt).scalars().all())
        for quote in quotes:
            quote.times_shown = 0
            quote.last_shown_date = None
        self.db.commit()
        return len(quotes)

    def get_pinned_quote(self) -> Optional[Quote]:
        """Get the currently pinned quote, if there is one."""
        stmt = select(Quote).where(Quote.pinned)
        return self.db.execute(stmt).scalars().first()

    def pin_quote(self, quote_id: int, pinned_date: date = None) -> Optional[Quote]:
        """Pin a specific quote, unpinning whatever was pinned before."""
        quote = self.db.get(Quote, quote_id)
        if not quote:
            return None

        self._clear_pins()
        quote.pinned = True
        quote.pinned_date = pinned_date or date.today()
        self.db.commit()
        return quote

    def unpin_quote(self) -> Optional[Quote]:
        """Remove the current pin. Returns the quote that was unpinned."""
        previous = self.get_pinned_quote()
        if previous:
            self._clear_pins()
            self.db.commit()
        return previous

    def cycle_pinned_quote(self, pinned_date: date = None) -> Optional[Quote]:
        """Replace the pinned quote with a different one chosen at random."""
        current = self.get_pinned_quote()

        stmt = select(Quote).where(Quote.active, Quote.pinned.is_(False))
        candidates = list(self.db.execute(stmt).scalars().all())

        if not candidates:
            return current

        # Picks which quote to pin; unpredictability is not a security property.
        chosen = random.choice(candidates)  # nosec B311
        self._clear_pins()
        chosen.pinned = True
        chosen.pinned_date = pinned_date or date.today()
        self.db.commit()
        return chosen

    def _clear_pins(self) -> None:
        """Unpin every pinned quote without committing."""
        stmt = select(Quote).where(Quote.pinned)
        for quote in self.db.execute(stmt).scalars().all():
            quote.pinned = False
            quote.pinned_date = None
