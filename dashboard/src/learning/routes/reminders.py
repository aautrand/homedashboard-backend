import json

from flask import Blueprint, current_app, jsonify, request

from dashboard.src.learning.learning_manager import ReminderManager
from dashboard.src.prints.print_manager import PrintManager

reminders_bp = Blueprint("reminders", __name__)


@reminders_bp.route("/reminder", methods=["POST"])
def create_reminder():
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "Missing required field: title"}), 400

    reminder_manager = ReminderManager(request.db)
    reminder = reminder_manager.add_reminder(
        title=data["title"],
        active=data.get("active", True),
    )

    return jsonify(reminder.to_dict()), 201


@reminders_bp.route("/reminder", methods=["GET"])
def get_reminders():
    reminder_manager = ReminderManager(request.db)

    active_param = request.args.get("active")
    if active_param is not None:
        active_lower = active_param.lower()
        if active_lower not in ("true", "false"):
            return jsonify({"error": "Invalid value for 'active'. Use 'true' or 'false'"}), 400
        is_active = active_lower == "true"
        reminders = reminder_manager.get_reminders_by_status(is_active)
    else:
        reminders = reminder_manager.get_all_reminders()

    response = [reminder.to_dict() for reminder in reminders]
    return jsonify(response)


@reminders_bp.route("/reminder/<int:reminder_id>", methods=["GET"])
def get_reminder(reminder_id):
    reminder_manager = ReminderManager(request.db)
    reminder = reminder_manager.get_reminder(reminder_id)

    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404

    return jsonify(reminder.to_dict())


@reminders_bp.route("/reminder/<int:reminder_id>", methods=["PUT"])
def update_reminder(reminder_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    reminder_manager = ReminderManager(request.db)
    reminder = reminder_manager.update_reminder(reminder_id, **data)

    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404

    return jsonify(reminder.to_dict())


@reminders_bp.route("/reminder/<int:reminder_id>", methods=["DELETE"])
def delete_reminder(reminder_id):
    reminder_manager = ReminderManager(request.db)
    reminder = reminder_manager.delete_reminder(reminder_id)

    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404

    return jsonify({"message": "Reminder deleted successfully"})


@reminders_bp.route("/reminder/<int:reminder_id>/print", methods=["POST"])
def print_reminder(reminder_id):
    reminder_manager = ReminderManager(request.db)
    reminder = reminder_manager.get_reminder(reminder_id)

    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404

    reminder_data = PrintManager.print_reminder(reminder)

    rabbit_client = current_app.config["message_broker_client"]
    rabbit_client.send_message(
        exchange="", routing_key="text_print", body=json.dumps(reminder_data)
    )

    return jsonify({"status": "ok"})