from abc import ABC, abstractmethod
from typing import List

from dashboard.src.calendar.clients.models.calendar_event import CalendarEvent


class CalendarMapper(ABC):
    @abstractmethod
    def map(self, raw) -> CalendarEvent:
        # Turn raw JSON into a CalendarEvent
        ...


class CalendarSequentialEventMapper(ABC):
    @abstractmethod
    def map(self, raw) -> List[CalendarEvent]: ...
