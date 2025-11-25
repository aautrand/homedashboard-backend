from datetime import date

from flask import Blueprint, jsonify, request

from dashboard.src.learning.learning_manager import RoutineTaskManager

routines_bp = Blueprint("routines", __name__)


@routines_bp.route("/routines", methods=["POST"])
def create_routine():
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "Missing required field: title"}), 400

    # Validate that at least one schedule type is provided
    if not data.get("schedule_pattern") and not data.get("interval_days"):
        return jsonify({"error": "Must provide either schedule_pattern or interval_days"}), 400

    routine_manager = RoutineTaskManager(request.db)
    routine = routine_manager.add_routine_task(
        title=data["title"],
        schedule_pattern=data.get("schedule_pattern"),
        interval_days=data.get("interval_days"),
        priority=data.get("priority", 0),
        active=data.get("active", True),
    )

    return jsonify(routine.to_dict()), 201


@routines_bp.route("/routines", methods=["GET"])
def get_routines():
    routine_manager = RoutineTaskManager(request.db)
    routines = routine_manager.get_all_routine_tasks()
    response = [routine.to_dict() for routine in routines]
    return jsonify(response)


@routines_bp.route("/routines/<int:routine_id>", methods=["GET"])
def get_routine(routine_id):
    routine_manager = RoutineTaskManager(request.db)
    routine = routine_manager.get_routine_task(routine_id)

    if not routine:
        return jsonify({"error": "Routine task not found"}), 404

    return jsonify(routine.to_dict())


@routines_bp.route("/routines/<int:routine_id>", methods=["PUT"])
def update_routine(routine_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    routine_manager = RoutineTaskManager(request.db)
    routine = routine_manager.update_routine_task(routine_id, **data)

    if not routine:
        return jsonify({"error": "Routine task not found"}), 404

    return jsonify(routine.to_dict())


@routines_bp.route("/routines/<int:routine_id>", methods=["DELETE"])
def delete_routine(routine_id):
    routine_manager = RoutineTaskManager(request.db)
    routine = routine_manager.delete_routine_task(routine_id)

    if not routine:
        return jsonify({"error": "Routine task not found"}), 404

    return jsonify({"message": "Routine task deleted successfully"})


@routines_bp.route("/routines/today", methods=["GET"])
def get_todays_routines():
    """Get all routine tasks that should be shown today."""
    routine_manager = RoutineTaskManager(request.db)
    today = date.today()
    routines = routine_manager.get_tasks_for_date(today)
    response = [routine.to_dict() for routine in routines]
    return jsonify(response)