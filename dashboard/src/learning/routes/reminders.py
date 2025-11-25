from flask import Blueprint, jsonify, request

from dashboard.src.learning.learning_manager import ReminderManager

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