import json
from datetime import datetime, time
from logging import getLogger

from flask import current_app

from dashboard.src.prints.receipts.formatter import ReceiptFormatter
from dashboard.src.prints.receipts.section import MultiElementSection

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
    def extract_birthdays_from_db(events):
        """Extract birthdays from CalendarEvent database objects."""
        birthdays = []
        non_birthday_events = []
        for event in events:
            if "birthday" in event.summary.lower():
                birthdays.append(event.summary.split(" ")[0].replace("'s", ""))
            else:
                non_birthday_events.append(event)
        return birthdays, non_birthday_events

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
    def extract_events_from_db(events, today_date):
        """Extract and categorize events from CalendarEvent database objects."""
        all_day_events = []
        timed_events = []

        for event in events:
            event_date = event.start_time.date()

            # Skip events that don't start today
            if event_date != today_date:
                continue

            # Categorize the event
            if event.start_time.hour == 0 and event.start_time.minute == 0:
                all_day_events.append(event.summary)
            else:
                time_str = event.start_time.strftime("%H:%M")
                timed_events.append((time_str, event.summary))

        timed_events.sort(
            key=lambda x: (
                x[0] == "",  # False (i.e. non-blank) comes before True
                datetime.strptime(x[0], "%H:%M").time() if x[0] else time.min,
            )
        )

        return all_day_events, timed_events

    @staticmethod
    def print_problems(problems):
        rabbit_client = current_app.config["message_broker_client"]

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
    def print_reminder(reminder):
        receipt_formatter = ReceiptFormatter()

        receipt_formatter.add_section(
            MultiElementSection(
                title=" Reminder ",
                items=[reminder.title],
                bullet="",
            )
        )

        final = receipt_formatter.build()
        return final

    @staticmethod
    def print_todo(todo):
        receipt_formatter = ReceiptFormatter()

        receipt_formatter.add_section(
            MultiElementSection(
                title=" To Do's ",
                items=[todo.title],
                bullet="[ ]",
            )
        )

        final = receipt_formatter.build()
        return final

    @staticmethod
    def print_event(event):
        """
        Build receipt data for a single calendar event.

        Args:
            event: CalendarEvent object

        Returns:
            Dictionary with formatted receipt data
        """
        receipt_formatter = ReceiptFormatter()

        # Format the event time
        if event.start_time.hour == 0 and event.start_time.minute == 0:
            time_str = "All Day"
        else:
            time_str = event.start_time.strftime("%H:%M")

        items = [
            f"{time_str} - {event.summary}",
        ]

        receipt_formatter.add_section(
            MultiElementSection(
                title=" Upcoming Event ",
                items=items,
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
    def build_pop_quiz(cards: list, quiz_id: int = None) -> dict:
        """
        Build the pop quiz receipt data from a list of cards.

        Args:
            cards: List of Card objects to include in the quiz
            quiz_id: Optional quiz ID to display on the receipt

        Returns:
            Dictionary with the formatted receipt data
        """
        receipt_formatter = ReceiptFormatter()
        now = datetime.now()

        if cards:
            card_items = []
            for card in cards:
                card_items.append(card.title)
                card_items.append("[ ]    [ ]    [ ]\n")
            receipt_formatter.add_section(
                MultiElementSection(
                    " Pop Quiz ",
                    card_items,
                    bullet="",
                )
            )

        # Format title with date, time, and quiz ID (e.g., "Dec 17, 2025 14:30 #42")
        title = (
            f"  {now.strftime('%b')} {now.day}, {now.year} {now.strftime('%H:%M')}  "
        )
        if quiz_id is not None:
            title = f"  {now.strftime('%b')} {now.day}, {now.year} {now.strftime('%H:%M')} #{quiz_id}  "
        return receipt_formatter.build(title=title)

    @staticmethod
    def build_pop_quiz_answers(cards: list) -> dict:
        """
        Build the pop quiz answers receipt data from a list of cards.

        Args:
            cards: List of Card objects to include answers for

        Returns:
            Dictionary with the formatted receipt data
        """
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

        return receipt_formatter.build()
