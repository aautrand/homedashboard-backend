import os

from caldav import DAVClient
from flask import current_app

from dashboard.src.calendar.clients.base import CalendarClient
from dashboard.src.calendar.clients.models.mappers.ical_mapper import (
    ICalCalendarSequentialEventMapper,
)


class ICalClient(CalendarClient):

    sequential_mapper = ICalCalendarSequentialEventMapper()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.BASE_URL = current_app.config["CALDAV_ICLOUD_URL"]
        self.username = current_app.config["APPLE_USER"]
        self.password = current_app.config["APPLE_DASHBOARD_SECRET"]

        self.client = DAVClient(
            url=self.BASE_URL, username=self.username, password=self.password
        )
        self.principal = self.client.principal()
        self.calendars = self.principal.calendars()

    def get_raw_events(self, calendars, start, end):
        today_events = []

        for calendar in self.calendars:
            if calendar.name in calendars:
                today_events.append(calendar.date_search(start, end))

        return today_events
