"""The backend services the home agent is allowed to call.

The agent depends on this container, not on how each service is built, so
tests can hand it stubs and the tools never reach for request or app globals.
"""

from dataclasses import dataclass

from dashboard.src.calendars.calendar_manager import CalendarEventManager
from dashboard.src.calendars.todo_manager import TodoManager
from dashboard.src.learning.learning_manager import CardManager
from dashboard.src.prints.printer import ReceiptPrinter, get_receipt_printer
from dashboard.src.quotes.quote_manager import QuoteManager
from dashboard.src.weather.weather_service import WeatherService, get_weather_service


@dataclass(frozen=True)
class HomeServices:
    todos: TodoManager
    calendar: CalendarEventManager
    weather: WeatherService
    quotes: QuoteManager
    cards: CardManager
    printer: ReceiptPrinter


def build_home_services(db) -> HomeServices:
    """Wire every service to one database session. Requires an app context."""
    return HomeServices(
        todos=TodoManager(db),
        calendar=CalendarEventManager(db),
        weather=get_weather_service(),
        quotes=QuoteManager(db),
        cards=CardManager(db),
        printer=get_receipt_printer(),
    )
