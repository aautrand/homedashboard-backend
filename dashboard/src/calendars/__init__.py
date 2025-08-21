from datetime import datetime, time

from flask import Blueprint, current_app

from dashboard.src.calendars.clients.base import get_calendar_client
from dashboard.src.calendars.helpers import get_text_calendar

calendar = Blueprint("calendar", __name__, url_prefix="/calendar")


@calendar.route("/text")
def text_calendar():
    text_calendar = get_text_calendar()
    return {"calendar": text_calendar}


@calendar.route("/events")
def current():
    calendar_client = get_calendar_client()
    today = datetime.today()
    start = datetime.combine(today, time(hour=0, minute=0))
    end = datetime.combine(today, time(hour=23, minute=59))
    calendars = [current_app.config["MAIN_CALENDAR"]]
    event_list = calendar_client.get_today_events(calendars, start, end)
    return {"events": event_list}
