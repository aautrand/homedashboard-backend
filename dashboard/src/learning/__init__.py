import json
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from dashboard.src.learning.learning_manager import (
    CardManager,
    ChecklistManager,
    RoutineTaskManager,
    SubjectManager,
    TopicManager,
)
from dashboard.src.learning.models.card import Card
from dashboard.src.message_broker.clients.base import get_message_broker_client
from dashboard.src.prints.print_manager import PrintManager

learning = Blueprint("learning", __name__, url_prefix="/learning")


@learning.route("/cards/<int:card_id>", methods=["PUT"])
def update_card(card_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    card_manager = CardManager(request.db)
    data["reviewed_date"] = datetime.now()
    data["reviewed"] = True
    card = card_manager.update_card(card_id, **data)

    if not card:
        return jsonify({"error": "Card not found"}), 404

    return jsonify(card.to_dict())


@learning.route("/cards", methods=["GET"])
def get_cards():
    card_manager = CardManager(request.db)
    reviewed = request.args.get("reviewed", None)

    if reviewed and reviewed.lower() == "false":
        cards = card_manager.get_non_reviewed_cards()
    else:
        cards = card_manager.get_all_cards()

    response = [card.to_json() for card in cards]
    return response


@learning.route("/problem", methods=["GET"])
def get_list_of_problems():
    # Get data from request
    reviewed = request.args.get("reviewed", None)
    if reviewed:
        stmt = select(Card).where(Card.reviewed == reviewed)
    else:
        stmt = select(Card)
    results = request.db.execute(stmt).scalars().all()
    response = [card.to_json() for card in results]
    return response


@learning.route("/topics", methods=["POST"])
def create_topic():
    data = request.get_json()

    if not data or "name" not in data or "subject_id" not in data:
        return jsonify({"error": "Missing required fields: name and subject_id"}), 400

    topic_manager = TopicManager(request.db)
    topic = topic_manager.add_topic(
        name=data["name"],
        subject_id=data["subject_id"],
        parent_topic_id=data.get("parent_topic_id"),
    )

    return jsonify({"id": topic.id, "name": topic.name}), 201


@learning.route("/subjects", methods=["POST"])
def create_subject():
    data = request.get_json()

    if not data or "name" not in data:
        return jsonify({"error": "Missing required field: name"}), 400

    subject_manager = SubjectManager(request.db)
    subject = subject_manager.add_subject(name=data["name"])

    return jsonify({"id": subject.id, "name": subject.name}), 201


@learning.route("/checklists", methods=["POST"])
def create_checklist():
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "Missing required field: title"}), 400

    checklist_manager = ChecklistManager(request.db)
    checklist = checklist_manager.add_checklist(
        title=data["title"], items=data.get("items", [])
    )

    return jsonify(checklist.to_dict()), 201


@learning.route("/checklists", methods=["GET"])
def get_checklists():
    checklist_manager = ChecklistManager(request.db)
    checklists = checklist_manager.get_all_checklists()
    response = [checklist.to_dict() for checklist in checklists]
    return jsonify(response)


@learning.route("/checklists/<int:checklist_id>", methods=["GET"])
def get_checklist(checklist_id):
    checklist_manager = ChecklistManager(request.db)
    checklist = checklist_manager.get_checklist(checklist_id)

    if not checklist:
        return jsonify({"error": "Checklist not found"}), 404

    return jsonify(checklist.to_dict())


@learning.route("/checklists/<int:checklist_id>", methods=["PUT"])
def update_checklist(checklist_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    checklist_manager = ChecklistManager(request.db)
    checklist = checklist_manager.update_checklist(checklist_id, **data)

    if not checklist:
        return jsonify({"error": "Checklist not found"}), 404

    return jsonify(checklist.to_dict())


@learning.route("/checklists/<int:checklist_id>", methods=["DELETE"])
def delete_checklist(checklist_id):
    checklist_manager = ChecklistManager(request.db)
    checklist = checklist_manager.delete_checklist(checklist_id)

    if not checklist:
        return jsonify({"error": "Checklist not found"}), 404

    return jsonify({"message": "Checklist deleted successfully"})


@learning.route("/checklists/<int:checklist_id>/print", methods=["POST"])
def print_checklist(checklist_id):
    checklist_manager = ChecklistManager(request.db)
    checklist = checklist_manager.get_checklist(checklist_id)

    if not checklist:
        return jsonify({"error": "Checklist not found"}), 404

    print_manager = PrintManager()
    checklist_data = print_manager.print_checklist(checklist)

    rabbit_client = get_message_broker_client()
    rabbit_client.send_message(
        exchange="", routing_key="text_print", body=json.dumps(checklist_data)
    )

    return jsonify({"status": "ok"})


@learning.route("/routines", methods=["POST"])
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


@learning.route("/routines", methods=["GET"])
def get_routines():
    routine_manager = RoutineTaskManager(request.db)
    routines = routine_manager.get_all_routine_tasks()
    response = [routine.to_dict() for routine in routines]
    return jsonify(response)


@learning.route("/routines/<int:routine_id>", methods=["GET"])
def get_routine(routine_id):
    routine_manager = RoutineTaskManager(request.db)
    routine = routine_manager.get_routine_task(routine_id)

    if not routine:
        return jsonify({"error": "Routine task not found"}), 404

    return jsonify(routine.to_dict())


@learning.route("/routines/<int:routine_id>", methods=["PUT"])
def update_routine(routine_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    routine_manager = RoutineTaskManager(request.db)
    routine = routine_manager.update_routine_task(routine_id, **data)

    if not routine:
        return jsonify({"error": "Routine task not found"}), 404

    return jsonify(routine.to_dict())


@learning.route("/routines/<int:routine_id>", methods=["DELETE"])
def delete_routine(routine_id):
    routine_manager = RoutineTaskManager(request.db)
    routine = routine_manager.delete_routine_task(routine_id)

    if not routine:
        return jsonify({"error": "Routine task not found"}), 404

    return jsonify({"message": "Routine task deleted successfully"})


@learning.route("/routines/today", methods=["GET"])
def get_todays_routines():
    """Get all routine tasks that should be shown today."""
    from datetime import date

    routine_manager = RoutineTaskManager(request.db)
    today = date.today()
    routines = routine_manager.get_tasks_for_date(today)
    response = [routine.to_dict() for routine in routines]
    return jsonify(response)


# TODO Add insert card endpoint
# TODO add review card endpoint
