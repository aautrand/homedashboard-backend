import json
from datetime import date, datetime, time, timezone
from logging import getLogger

from flask import current_app, request

from dashboard.src.calendars import get_calendar_client
from dashboard.src.learning.learning_manager import CardManager, ReminderManager, RoutineTaskManager, SubjectManager
from dashboard.src.message_broker.clients.base import get_message_broker_client
from dashboard.src.prints.receipts.formatter import ReceiptFormatter
from dashboard.src.prints.receipts.section import MultiElementSection
from dashboard.src.weather.clients.base import get_weather_client
from dashboard.src.weather.clients.models.open_weather import OpenWeather

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
    def extract_events(events, today_date):
        all_day_events = []
        timed_events = []
        calendar_events = []
        for raw in events[:]:
            data = json.loads(raw)
            start_time_str = data["start_time"]

            # Parse the start time - handle both date-only and datetime formats
            if "T" in start_time_str:
                dt = datetime.fromisoformat(start_time_str)
                event_date = dt.date()
            else:
                # Date-only format (all-day events)
                event_date = datetime.fromisoformat(start_time_str).date()

            # Skip events that don't start today
            if event_date != today_date:
                events.remove(raw)
                continue

            # Categorize the event
            if "T" in start_time_str:
                dt = datetime.fromisoformat(start_time_str)
                if dt.hour == 0 and dt.minute == 0:
                    all_day_events.append(data["summary"])
                else:
                    time_str = dt.strftime("%H:%M")
                    timed_events.append((time_str, data["summary"]))
            else:
                # Date-only events are all-day events
                all_day_events.append(data["summary"])

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

        # Use naive datetime (no timezone info) for CalDAV queries
        today = datetime.now()

        start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end = today.replace(hour=23, minute=59, second=58, microsecond=0)
        print(today, start, end)

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
        today_date = today.date()
        all_day_events, timed_events, calendar_events = PrintManager.extract_events(
            event_list, today_date
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

        # Insert routine tasks
        routine_manager = RoutineTaskManager(request.db)
        routine_tasks = routine_manager.get_tasks_for_date(today_date)

        if routine_tasks:
            # Mark interval-based tasks as shown
            for task in routine_tasks:
                if task.interval_days:
                    routine_manager.mark_task_shown(task.id, today_date)

            # Format tasks with checkboxes
            routine_items = [f"[ ] {task.title}" for task in routine_tasks]
            receipt_formatter.add_section(
                MultiElementSection(
                    " Routines ",
                    routine_items,
                    bullet="",
                )
            )

        # Insert reminders
        reminder_manager = ReminderManager(request.db)
        active_reminders = reminder_manager.get_active_reminders()

        if active_reminders:
            # Mark reminders as shown
            for reminder in active_reminders:
                reminder_manager.mark_reminder_shown(reminder.id, today_date)

            reminder_items = [reminder.title for reminder in active_reminders]
            receipt_formatter.add_section(
                MultiElementSection(
                    " Reminders ",
                    reminder_items,
                    bullet="!",
                )
            )

        # Insert studies (spaced repetition)
        subject_manager = SubjectManager(request.db)
        study_subjects = subject_manager.get_subjects_for_study_today(today_date, max_subjects=1)

        if study_subjects:
            # Mark subjects as studied
            for subject in study_subjects:
                subject_manager.mark_subject_studied(subject.id, today_date)

            study_items = [f"Study: {subject.name}" for subject in study_subjects]
            receipt_formatter.add_section(
                MultiElementSection(
                    " Today's Study ",
                    study_items,
                    bullet="*",
                )
            )

        # Insert questions
        card_manager = CardManager(request.db)
        non_grokked_cards = card_manager.get_non_grokked_cards()

        if non_grokked_cards:
            card_items = [card.title for card in non_grokked_cards]
            receipt_formatter.add_section(
                MultiElementSection(
                    " Pop Quiz ",
                    card_items,
                    bullet="-",
                )
            )

        # Insert tasks
        final = receipt_formatter.build()
        return final

    @staticmethod
    def print_problems(problems):
        rabbit_client = get_message_broker_client()

        rabbit_client.send_message(
            exchange="", routing_key="image_print", body=json.dumps(problems)
        )

    @staticmethod
    def print_checklist(checklist):
        receipt_formatter = ReceiptFormatter()

        # Add checklist items as a section with checkboxes
        checklist_items = [f"[ ] {item}" for item in checklist.items]
        receipt_formatter.add_section(
            MultiElementSection(
                title=f" {checklist.title} ",
                items=checklist_items,
                bullet="",
            )
        )

        final = receipt_formatter.build()
        return final

    @staticmethod
    def print_text(text):

        receipt_formatter = ReceiptFormatter()

        # Add checklist items as a section with checkboxes
        receipt_formatter.add_section(
            MultiElementSection(
                title=f"",
                items=text,
                bullet="",
            )
        )

        final = receipt_formatter.build("")
        return final

    @staticmethod
    def print_text_delayed(text):

        receipt_formatter = ReceiptFormatter()

        # Add checklist items as a section with checkboxes
        receipt_formatter.add_section(
            MultiElementSection(
                title=f"",
                items=text,
                bullet="",
            )
        )

        final = receipt_formatter.build("")
        return final

    @staticmethod
    def print_pop_quiz():
        receipt_formatter = ReceiptFormatter()
        now = datetime.now()

        # Insert questions
        card_manager = CardManager(request.db)
        non_grokked_cards = card_manager.get_non_grokked_cards()

        if non_grokked_cards:
            card_items = []
            for card in non_grokked_cards:
                card_items.append(card.title)
                card_items.append("[ ]    [ ]    [ ]\n")
            receipt_formatter.add_section(
                MultiElementSection(
                    " Pop Quiz ",
                    card_items,
                    bullet="",
                )
            )

        # Format title with date and time (e.g., "Dec 17, 2025 14:30")
        title = f"  {now.strftime('%b')} {now.day}, {now.year} {now.strftime('%H:%M')}  "
        final = receipt_formatter.build(title=title)
        return final, non_grokked_cards

    @staticmethod
    def print_pop_quiz_answers(cards):
        receipt_formatter = ReceiptFormatter()

        if cards:
            answer_items = []
            for card in cards:
                answer_items.append(f"{card.title}")
                answer_items.append(f"  {card.content}\n")
            receipt_formatter.add_section(
                MultiElementSection(
                    " Pop Quiz Answers ",
                    answer_items,
                    bullet="",
                )
            )

        final = receipt_formatter.build()
        return final