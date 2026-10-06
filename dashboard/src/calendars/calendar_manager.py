import json
from datetime import date, datetime, time, timedelta
from typing import List, Optional

from flask import current_app
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from dashboard.src.calendars.clients.base import get_calendar_client
from dashboard.src.calendars.models.calendar_event import CalendarEvent


class CalendarEventManager:
    """Manager for syncing and querying calendar events from the database."""

    def __init__(self, db: Session):
        self.db = db

    def sync_events(
        self,
        calendars: List[str],
        start: datetime,
        end: datetime,
    ) -> dict:
        """
        Sync calendar events from CalDAV to the database.

        Fetches events from the CalDAV server and synchronizes them with the database:
        - New events are inserted
        - Changed events are updated
        - Events no longer in CalDAV (within the date range) are deleted

        Args:
            calendars: List of calendar names to sync
            start: Start datetime for the sync range
            end: End datetime for the sync range

        Returns:
            Dictionary with sync statistics:
                - inserted: number of new events
                - updated: number of updated events
                - deleted: number of deleted events
                - total: total events in range after sync
        """
        # Fetch events from CalDAV
        calendar_client = get_calendar_client()
        raw_events = calendar_client.get_today_events(calendars, start, end)

        # Parse the JSON events into dictionaries
        caldav_events = {}
        for raw in raw_events:
            event_data = json.loads(raw)
            uid = event_data["uid"]
            caldav_events[uid] = event_data

        # Get existing events by UID (not by date range) to handle date changes
        existing_events = self._get_events_by_uids(list(caldav_events.keys()))
        existing_by_uid = {event.uid: event for event in existing_events}

        inserted = 0
        updated = 0
        deleted = 0

        # Process CalDAV events
        for uid, event_data in caldav_events.items():
            if uid in existing_by_uid:
                # Update existing event if changed
                db_event = existing_by_uid[uid]
                if self._event_changed(db_event, event_data):
                    self._update_event(db_event, event_data)
                    updated += 1
                # Remove from existing_by_uid so we know what's left to delete
                del existing_by_uid[uid]
            else:
                # Insert new event
                self._insert_event(event_data)
                inserted += 1

        # Delete events that are no longer in CalDAV
        for uid, db_event in existing_by_uid.items():
            # Only delete if the event's start_time is within our sync range
            # This prevents deleting events outside the sync range
            if start <= db_event.start_time <= end:
                self.db.delete(db_event)
                deleted += 1

        self.db.commit()

        # Get final count
        total = len(self._get_events_in_range(start, end))

        return {
            "inserted": inserted,
            "updated": updated,
            "deleted": deleted,
            "total": total,
        }

    def sync_today(self, calendars: List[str] = None) -> dict:
        """
        Convenience method to sync events for today.

        Args:
            calendars: List of calendar names. If None, uses default calendars.

        Returns:
            Sync statistics dictionary
        """
        return self.sync_date(datetime.now().date(), calendars)

    def sync_date(self, target_date: date, calendars: List[str] = None) -> dict:
        """
        Sync events for a single day.

        Args:
            target_date: The day to sync.
            calendars: List of calendar names. If None, uses default calendars.

        Returns:
            Sync statistics dictionary
        """
        if calendars is None:
            calendars = [current_app.config["MAIN_CALENDAR"], "Chores"]

        start = datetime.combine(target_date, time(hour=0, minute=0, second=0))
        end = datetime.combine(target_date, time(hour=23, minute=59, second=59))

        return self.sync_events(calendars, start, end)

    def get_synced_events_for_date(
        self, target_date: date, calendars: List[str] = None
    ) -> List[CalendarEvent]:
        """
        Pull a day's events from CalDAV, then return them from the database.

        Use this when the answer has to be current (e.g. a voice query about
        tomorrow), since stored events are only as fresh as the last sync.

        Args:
            target_date: The day to fetch.
            calendars: List of calendar names. If None, uses default calendars.

        Returns:
            List of CalendarEvent objects
        """
        self.sync_date(target_date, calendars)
        return self.get_events_for_date(target_date)

    def get_events_for_date(self, target_date: date) -> List[CalendarEvent]:
        """
        Get all events for a specific date from the database.

        Args:
            target_date: The date to get events for

        Returns:
            List of CalendarEvent objects
        """
        start = datetime.combine(target_date, time(hour=0, minute=0, second=0))
        end = datetime.combine(target_date, time(hour=23, minute=59, second=59))
        return self._get_events_in_range(start, end)

    def get_events_starting_between(
        self,
        start: datetime,
        end: datetime,
    ) -> List[CalendarEvent]:
        """
        Get events that start between the given datetimes.

        Useful for upcoming event notifications (e.g., events starting in next 10 min).

        Args:
            start: Start of the time window
            end: End of the time window

        Returns:
            List of CalendarEvent objects starting in that window
        """
        stmt = (
            select(CalendarEvent)
            .where(
                and_(
                    CalendarEvent.start_time >= start,
                    CalendarEvent.start_time <= end,
                )
            )
            .order_by(CalendarEvent.start_time)
        )
        return self.db.execute(stmt).scalars().all()

    def get_upcoming_events(self, minutes: int = 10) -> List[CalendarEvent]:
        """
        Get events starting in the next N minutes.

        Args:
            minutes: Number of minutes to look ahead (default 10)

        Returns:
            List of CalendarEvent objects starting soon
        """
        now = datetime.now()
        end = now + timedelta(minutes=minutes)
        return self.get_events_starting_between(now, end)

    def get_all_events(self) -> List[CalendarEvent]:
        """Get all stored calendar events."""
        stmt = select(CalendarEvent).order_by(CalendarEvent.start_time)
        return self.db.execute(stmt).scalars().all()

    def get_event_by_uid(self, uid: str) -> Optional[CalendarEvent]:
        """Get a specific event by its UID."""
        stmt = select(CalendarEvent).where(CalendarEvent.uid == uid)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_next_timed_event(self) -> Optional[CalendarEvent]:
        """
        Get the next upcoming event that has a specific time (not all-day).

        All-day events have start_time at midnight (00:00). This method
        excludes those and returns the next event with an actual time.

        Returns:
            The next timed CalendarEvent, or None if no upcoming events
        """
        now = datetime.now()
        stmt = (
            select(CalendarEvent)
            .where(
                and_(
                    CalendarEvent.start_time > now,
                    # Exclude all-day events (midnight start times)
                    ~and_(
                        CalendarEvent.start_time == CalendarEvent.start_time,
                        # Check hour and minute are not both 0
                    ),
                )
            )
            .order_by(CalendarEvent.start_time)
        )
        events = self.db.execute(stmt).scalars().all()

        # Filter out all-day events (those starting at midnight)
        for event in events:
            if not (event.start_time.hour == 0 and event.start_time.minute == 0):
                return event

        return None

    def get_unnotified_events_starting_soon(
        self,
        minutes: int = 15,
    ) -> List[CalendarEvent]:
        """
        Get events starting within the next N minutes that haven't been notified.

        This is designed for periodic polling (e.g., N8N calling every 10 min).
        Only returns events that:
        - Start within the specified time window
        - Have not been notified (notified_at is NULL)
        - Are not all-day events

        Args:
            minutes: Number of minutes to look ahead (default 15)

        Returns:
            List of CalendarEvent objects that need notification
        """
        now = datetime.now()
        end = now + timedelta(minutes=minutes)

        stmt = (
            select(CalendarEvent)
            .where(
                and_(
                    CalendarEvent.start_time >= now,
                    CalendarEvent.start_time <= end,
                    CalendarEvent.notified_at.is_(None),
                )
            )
            .order_by(CalendarEvent.start_time)
        )
        events = self.db.execute(stmt).scalars().all()

        # Filter out all-day events
        return [
            e
            for e in events
            if not (e.start_time.hour == 0 and e.start_time.minute == 0)
        ]

    def mark_event_notified(self, event_id: int) -> None:
        """
        Mark an event as notified by setting notified_at to now.

        Args:
            event_id: The ID of the event to mark as notified
        """
        stmt = select(CalendarEvent).where(CalendarEvent.id == event_id)
        event = self.db.execute(stmt).scalar_one_or_none()
        if event:
            event.notified_at = datetime.now()
            self.db.commit()

    def _get_events_in_range(
        self,
        start: datetime,
        end: datetime,
    ) -> List[CalendarEvent]:
        """Get events from database where start_time is within the range."""
        stmt = (
            select(CalendarEvent)
            .where(
                and_(
                    CalendarEvent.start_time >= start,
                    CalendarEvent.start_time <= end,
                )
            )
            .order_by(CalendarEvent.start_time)
        )
        return self.db.execute(stmt).scalars().all()

    def _get_events_by_uids(self, uids: List[str]) -> List[CalendarEvent]:
        """Get events from database that match any of the given UIDs."""
        if not uids:
            return []
        stmt = select(CalendarEvent).where(CalendarEvent.uid.in_(uids))
        return self.db.execute(stmt).scalars().all()

    def _event_changed(self, db_event: CalendarEvent, caldav_data: dict) -> bool:
        """Check if the CalDAV event data differs from the database event."""
        # Parse the start and end times from the CalDAV data
        caldav_start = self._parse_datetime(caldav_data["start_time"])
        caldav_end = self._parse_datetime(caldav_data["end_time"])

        # Compare fields
        if db_event.summary != caldav_data["summary"]:
            return True
        if db_event.calendar != caldav_data["calendar"]:
            return True
        if db_event.recurring != caldav_data["recurring"]:
            return True
        # Compare datetimes (need to handle timezone awareness)
        if self._datetimes_differ(db_event.start_time, caldav_start):
            return True
        if self._datetimes_differ(db_event.end_time, caldav_end):
            return True

        return False

    def _datetimes_differ(self, dt1: datetime, dt2: datetime) -> bool:
        """Compare two datetimes, handling timezone awareness differences."""
        # Make both naive for comparison if needed
        if dt1.tzinfo is not None:
            dt1 = dt1.replace(tzinfo=None)
        if dt2.tzinfo is not None:
            dt2 = dt2.replace(tzinfo=None)
        return dt1 != dt2

    def _update_event(self, db_event: CalendarEvent, caldav_data: dict) -> None:
        """Update a database event with CalDAV data."""
        db_event.summary = caldav_data["summary"]
        db_event.calendar = caldav_data["calendar"]
        db_event.recurring = caldav_data["recurring"]
        db_event.start_time = self._parse_datetime(caldav_data["start_time"])
        db_event.end_time = self._parse_datetime(caldav_data["end_time"])
        db_event.last_synced = datetime.now()

    def _insert_event(self, caldav_data: dict) -> CalendarEvent:
        """Insert a new event into the database."""
        event = CalendarEvent(
            uid=caldav_data["uid"],
            calendar=caldav_data["calendar"],
            summary=caldav_data["summary"],
            recurring=caldav_data["recurring"],
            start_time=self._parse_datetime(caldav_data["start_time"]),
            end_time=self._parse_datetime(caldav_data["end_time"]),
        )
        self.db.add(event)
        return event

    def _parse_datetime(self, dt_string: str) -> datetime:
        """Parse an ISO format datetime string."""
        # Handle both date-only and datetime formats
        if "T" in dt_string:
            dt = datetime.fromisoformat(dt_string)
            # Store as naive datetime (remove timezone info)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        else:
            # Date-only format - treat as midnight
            return datetime.fromisoformat(dt_string)
