from abc import ABC, abstractmethod
from typing import List

from dashboard.src.calendar.clients.models.calendar_event import CalendarEvent
from dashboard.src.calendar.clients.models.mappers.base import (
    CalendarMapper,
    CalendarSequentialEventMapper,
)


class CalendarClient(ABC):
    mapper: CalendarMapper
    sequential_mapper: CalendarSequentialEventMapper

    @abstractmethod
    def get_raw_events(self, calendars, start, end): ...

    def get_today_events(self, calendars, start, end) -> List[CalendarEvent]:
        raw = self.get_raw_events(calendars, start, end)
        return self.sequential_mapper.map(raw)


def get_calendar_client(source: str = "ical") -> CalendarClient:
    if source == "ical":
        from .ical_client import ICalClient

        return ICalClient()
    else:
        raise ValueError(f"Unknown source: {source}")
