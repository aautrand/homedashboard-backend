import json

from flask import Blueprint, current_app, jsonify, request

from dashboard.src.learning.learning_manager import ChecklistManager
from dashboard.src.prints.print_manager import PrintManager

checklists_bp = Blueprint("checklists", __name__)


@checklists_bp.route("/checklists", methods=["POST"])
def create_checklist():
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "Missing required field: title"}), 400

    checklist_manager = ChecklistManager(request.db)
    checklist = checklist_manager.add_checklist(
        title=data["title"], items=data.get("items", [])
    )

    return jsonify(checklist.to_dict()), 201


@checklists_bp.route("/checklists", methods=["GET"])
def get_checklists():
    checklist_manager = ChecklistManager(request.db)
    checklists = checklist_manager.get_all_checklists()
    response = [checklist.to_dict() for checklist in checklists]
    return jsonify(response)


@checklists_bp.route("/checklists/<int:checklist_id>", methods=["GET"])
def get_checklist(checklist_id):
    checklist_manager = ChecklistManager(request.db)
    checklist = checklist_manager.get_checklist(checklist_id)

    if not checklist:
        return jsonify({"error": "Checklist not found"}), 404

    return jsonify(checklist.to_dict())


@checklists_bp.route("/checklists/<int:checklist_id>", methods=["PUT"])
def update_checklist(checklist_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    checklist_manager = ChecklistManager(request.db)
    checklist = checklist_manager.update_checklist(checklist_id, **data)

    if not checklist:
        return jsonify({"error": "Checklist not found"}), 404

    return jsonify(checklist.to_dict())


@checklists_bp.route("/checklists/<int:checklist_id>", methods=["DELETE"])
def delete_checklist(checklist_id):
    checklist_manager = ChecklistManager(request.db)
    checklist = checklist_manager.delete_checklist(checklist_id)

    if not checklist:
        return jsonify({"error": "Checklist not found"}), 404

    return jsonify({"message": "Checklist deleted successfully"})


@checklists_bp.route("/checklists/<int:checklist_id>/print", methods=["POST"])
def print_checklist(checklist_id):
    checklist_manager = ChecklistManager(request.db)
    checklist = checklist_manager.get_checklist(checklist_id)

    if not checklist:
        return jsonify({"error": "Checklist not found"}), 404

    print_manager = PrintManager()
    checklist_data = print_manager.print_checklist(checklist)

    rabbit_client = current_app.config["message_broker_client"]
    rabbit_client.send_message(
        exchange="", routing_key="text_print", body=json.dumps(checklist_data)
    )

    return jsonify({"status": "ok"})