import json
from datetime import datetime, time

from flask import Blueprint, current_app, jsonify, request

from dashboard.src.calendars.calendar_manager import CalendarEventManager
from dashboard.src.calendars.clients.base import get_calendar_client
from dashboard.src.calendars.helpers import get_text_calendar
from dashboard.src.calendars.todo_manager import TodoManager
from dashboard.src.prints.print_manager import PrintManager

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


@calendar.route("/sync", methods=["POST"])
def sync_calendar():
    """
    Sync calendar events from CalDAV to the database.

    This endpoint fetches events from the configured CalDAV calendars
    and synchronizes them with the local database. It handles:
    - Inserting new events
    - Updating changed events
    - Deleting events that no longer exist in CalDAV

    Returns:
        JSON with sync statistics (inserted, updated, deleted, total)
    """

    calendar_manager = CalendarEventManager(request.db)
    calendars = [current_app.config["MAIN_CALENDAR"], "Chores"]

    today = datetime.now()
    start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end = today.replace(hour=23, minute=59, second=59, microsecond=0)

    result = calendar_manager.sync_events(calendars, start, end)
    return {
        "status": "ok",
        "sync_result": result,
    }


@calendar.route("/events/stored")
def stored_events():
    """
    Get calendar events from the database.

    Returns events that have been synced to the local database,
    rather than fetching directly from CalDAV.
    """

    calendar_manager = CalendarEventManager(request.db)
    today = datetime.today().date()
    events = calendar_manager.get_events_for_date(today)
    return {
        "events": [event.to_dict() for event in events],
    }


@calendar.route("/events/print-next", methods=["POST"])
def print_next_event():
    """
    Print the next upcoming timed calendar event.

    This endpoint prints the next event that has a specific time
    (excludes all-day events). Use this for on-demand "what's next" queries.

    Returns:
        JSON with status and event details (if any)
    """
    calendar_manager = CalendarEventManager(request.db)

    # Get the next timed event
    event = calendar_manager.get_next_timed_event()

    if not event:
        return {
            "status": "ok",
            "printed": False,
            "message": "No upcoming timed events found",
        }

    rabbit_client = current_app.config["message_broker_client"]
    event_data = PrintManager.print_event(event)
    rabbit_client.send_message(
        exchange="", routing_key="text_print", body=json.dumps(event_data)
    )

    return {
        "status": "ok",
        "printed": True,
        "event": event.to_dict(),
        "message": f"Printed: {event.summary} at {event.start_time.strftime('%H:%M')}",
    }


@calendar.route("/events/notify-upcoming", methods=["POST"])
def notify_upcoming_events():
    """
    Check for and print events starting soon that haven't been notified.

    This endpoint is designed for periodic polling (e.g., N8N calling every 10 min).
    It checks for events starting within the next 15 minutes that haven't been
    printed yet, prints them, and marks them as notified.

    Query parameters:
        minutes: Number of minutes to look ahead (default 15)

    Returns:
        JSON with status and list of notified events
    """
    minutes = request.args.get("minutes", 90, type=int)
    calendar_manager = CalendarEventManager(request.db)

    # First sync today's events to ensure we have the latest
    calendars = [current_app.config["MAIN_CALENDAR"], "Chores"]
    today = datetime.now()
    calendar_manager.sync_events(
        calendars,
        today.replace(hour=0, minute=0, second=0, microsecond=0),
        today.replace(hour=23, minute=59, second=59, microsecond=0),
    )

    # Get unnotified events starting soon
    events = calendar_manager.get_unnotified_events_starting_soon(minutes=minutes)

    if not events:
        return {
            "status": "ok",
            "printed_count": 0,
            "events": [],
            "message": "No upcoming events to notify",
        }
    rabbit_client = current_app.config["message_broker_client"]
    notified_events = []

    for event in events:
        event_data = PrintManager.print_event(event)
        rabbit_client.send_message(
            exchange="", routing_key="text_print", body=json.dumps(event_data)
        )
        calendar_manager.mark_event_notified(event.id)
        notified_events.append(event.to_dict())

    return {
        "status": "ok",
        "printed_count": len(notified_events),
        "events": notified_events,
        "message": f"Printed {len(notified_events)} upcoming event(s)",
    }


@calendar.route("/todo", methods=["POST"])
def create_todo():
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "Missing required field: title"}), 400

    todo_manager = TodoManager(request.db)
    todo = todo_manager.add_todo(
        title=data["title"],
        active=data.get("active", True),
    )

    return jsonify(todo.to_dict()), 201


@calendar.route("/todo", methods=["GET"])
def get_todos():
    todo_manager = TodoManager(request.db)

    active_param = request.args.get("active")
    if active_param is not None:
        active_lower = active_param.lower()
        if active_lower not in ("true", "false"):
            return (
                jsonify({"error": "Invalid value for 'active'. Use 'true' or 'false'"}),
                400,
            )
        is_active = active_lower == "true"
        todos = todo_manager.get_todos_by_status(is_active)
    else:
        todos = todo_manager.get_all_todos()

    response = [todo.to_dict() for todo in todos]
    return jsonify(response)


@calendar.route("/todo/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    todo_manager = TodoManager(request.db)
    todo = todo_manager.get_todo(todo_id)

    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    return jsonify(todo.to_dict())


@calendar.route("/todo/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    todo_manager = TodoManager(request.db)
    todo = todo_manager.update_todo(todo_id, **data)

    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    return jsonify(todo.to_dict())


@calendar.route("/todo/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    todo_manager = TodoManager(request.db)
    todo = todo_manager.delete_todo(todo_id)

    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    return jsonify({"message": "Todo deleted successfully"})


@calendar.route("/todo/<int:todo_id>/print", methods=["POST"])
def print_todo(todo_id):
    todo_manager = TodoManager(request.db)
    todo = todo_manager.get_todo(todo_id)

    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    todo_data = PrintManager.print_todo(todo)

    rabbit_client = current_app.config["message_broker_client"]
    rabbit_client.send_message(
        exchange="", routing_key="text_print", body=json.dumps(todo_data)
    )

    return jsonify({"status": "ok"})
