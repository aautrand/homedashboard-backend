from typing import List

from ..calendar_event import CalendarEvent
from .base import CalendarSequentialEventMapper


class ICalCalendarSequentialEventMapper(CalendarSequentialEventMapper):
    def map(self, raw) -> List[str]:
        event_list = []

        for calendar in raw:
            for event in calendar:
                vevent = event.vobject_instance.vevent
                sum = vevent.summary.value
                is_recurring = "recurrence-id" in vevent.contents.keys()
                # Get the UID - for recurring events, append recurrence-id to make it unique
                uid = vevent.uid.value
                if is_recurring:
                    recurrence_id = vevent.contents.get("recurrence-id", [None])[0]
                    if recurrence_id:
                        uid = f"{uid}_{recurrence_id.value.isoformat()}"
                calendar_event = CalendarEvent(
                    uid=uid,
                    calendar=event.parent.name,
                    summary=sum,
                    recurring=is_recurring,
                    start_time=vevent.dtstart.value.isoformat(),
                    end_time=vevent.dtend.value.isoformat(),
                )
                event_list.append(calendar_event.to_json())
        return event_list
