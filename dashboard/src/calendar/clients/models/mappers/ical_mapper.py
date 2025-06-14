from .base import CalendarSequentialEventMapper
from ..calendar_event import CalendarEvent
from typing import List


class ICalCalendarSequentialEventMapper(CalendarSequentialEventMapper):
    def map(self, raw) -> List[str]:
        event_list = []

        for calendar in raw:
            for event in calendar:
                vevent = event.vobject_instance.vevent
                sum = vevent.summary.value
                is_recurring = "recurrence-id" in vevent.contents.keys()
                calendar_event = CalendarEvent(calendar=event.parent.name,
                                               summary=sum,
                                               recurring=is_recurring,
                                               start_time=vevent.dtstart.value.isoformat(),
                                               end_time=vevent.dtend.value.isoformat())
                event_list.append(calendar_event.to_json())
        return event_list