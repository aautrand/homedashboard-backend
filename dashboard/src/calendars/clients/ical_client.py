from caldav import DAVClient
from flask import current_app

from dashboard.src.calendars.clients.base import CalendarClient
import dashboard.src.calendars.clients.models.mappers.ical_mapper


class ICalClient(CalendarClient):

    sequential_mapper = dashboard.src.calendars.clients.models.mappers.ical_mapper.ICalCalendarSequentialEventMapper()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.BASE_URL = current_app.config["CALDAV_ICLOUD_URL"]
        self.username = current_app.config["APPLE_USER"]
        self.password = current_app.config["APPLE_DASHBOARD_SECRET"]
        self.client = DAVClient(
            url=self.BASE_URL, username=self.username, password=self.password
        )

    def get_raw_events(self, calendars, start, end):
        principal = self.client.principal()
        principal_calendars = principal.calendars()

        today_events = []

        for calendar in principal_calendars:
            if calendar.name in calendars:
                today_events.append(calendar.date_search(start, end))

        return today_events
