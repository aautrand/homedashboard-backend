import json
import os
from datetime import datetime, time

from flask import current_app

from dashboard.src.calendar import get_calendar_client
from dashboard.src.prints.receipts.formatter import ReceiptFormatter
from dashboard.src.prints.receipts.section import MultiElementSection
from dashboard.src.utils.helpers import latex_to_png, scp_files
from dashboard.src.weather.clients.base import get_weather_client
from dashboard.src.weather.clients.models.open_weather import OpenWeather
from logging import getLogger


logger = getLogger(__name__)


class PrintManager:

    @staticmethod
    def extract_weather(weather):
        weather_conditions = ", ".join(w.description for w in weather.weather)

        items = [
            f"Current:               {int(weather.main.temp)}C / {int((weather.main.temp * 1.8) + 32)}F",
            f"Forecast (Celsius):    {int(weather.daily_min_temp)} / {int(weather.daily_max_temp)}",
            f"Forecast (Fahrenheit): {int((weather.daily_min_temp * 1.8) + 32)} / {int((weather.daily_max_temp * 1.8) + 32)}",
            f"Forecast Conditions:   {weather_conditions}",
        ]
        return items

    @staticmethod
    def extract_birthdays(events):
        birthdays = []
        for event in events:
            json_events = json.loads(event)
            if "birthday" in json_events["summary"].lower():
                birthdays.append(json_events["summary"].split(" ")[0].replace("'s", ""))
                events.remove(event)
        return birthdays

    @staticmethod
    def extract_events(events):
        all_day_events = []
        timed_events = []
        calendar_events = []
        for raw in events[:]:
            data = json.loads(raw)
            dt = datetime.fromisoformat(data["start_time"])
            # blank out midnight; otherwise HH:MM
            if dt.hour == 0 and dt.minute == 0:
                all_day_events.append(data["summary"])
            else:
                time_str = dt.strftime("%H:%M")
                timed_events.append((time_str, data["summary"]))
            events.remove(raw)

        timed_events.sort(
            key=lambda x: (
                x[0] == "",  # False (i.e. non-blank) comes before True
                datetime.strptime(x[0], "%H:%M").time() if x[0] else time.min,
            )
        )

        return all_day_events, timed_events, calendar_events

    @staticmethod
    def print_tasks():
        receipt_formatter = ReceiptFormatter()

        # weather
        weather_client = get_weather_client("open-weather")
        current_weather = weather_client.get_current_weather(
            current_app.config["LAT_LONG"]
        )
        forecast_weather = weather_client.get_forecast_weather(
            current_app.config["LAT_LONG"]
        )
        weather = OpenWeather.from_current_and_forecast(
            current_weather, forecast_weather
        )

        weather_items = PrintManager.extract_weather(weather)
        receipt_formatter.add_section(
            MultiElementSection(
                title="Weather",
                items=weather_items,
                bullet="",
            )
        )

        # get calendar events
        calendar_client = get_calendar_client()

        # today = datetime.today()
        today = datetime.today()
        start = datetime.combine(today, time(hour=0, minute=0))
        end = datetime.combine(today, time(hour=23, minute=59))
        logger.info(f"start: {start}, end: {end}, today: {today}")
        calendars = [current_app.config["MAIN_CALENDAR"], "Chores"]
        logger.info(f"calendars: {calendars}")
        event_list = calendar_client.get_today_events(calendars, start, end)
        logger.info(f"event_list: {event_list}")

        # Insert birthdays
        birthdays = PrintManager.extract_birthdays(event_list)
        if birthdays:
            receipt_formatter.add_section(MultiElementSection(" Birthdays ", birthdays))

        # Insert calendar events
        all_day_events, timed_events, calendar_events = PrintManager.extract_events(
            event_list
        )
        if all_day_events:
            receipt_formatter.add_section(
                MultiElementSection(
                    " All Day Events ",
                    all_day_events,
                    bullet="-",
                )
            )

        if timed_events:
            receipt_formatter.add_section(
                MultiElementSection(
                    " Calendar ",
                    timed_events,
                    bullet="*",
                    formatter=lambda t: f"{t[0]} - {t[1]}",
                )
            )

        # TODO Insert chores
        # Insert tasks
        final = receipt_formatter.build()
        return final

    @staticmethod
    def print_problems(formulas):
        out_dir = "/tmp"
        files = []
        for i, expr in enumerate(formulas, start=1):
            fname = os.path.join(out_dir, f"item_{i:02d}.png")
            files.append(fname)
            latex_to_png(expr, i, fname, fontsize=9, dpi=300, pad_inches=0.05)

        scp_files(files, "printer", "printers", "/tmp/")
