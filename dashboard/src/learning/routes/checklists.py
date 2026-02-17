import json

from flask import Blueprint, current_app, jsonify, request

from dashboard.src.learning.learning_manager import ChecklistManager
from dashboard.src.prints.print_manager import PrintManager

checklists_bp = Blueprint("checklists", __name__)


@checklists_bp.route("/checklists", methods=["POST"])
def create_checklist():
    """Create a new checklist with a title and optional items.

    Request body (JSON):
        title (str): Required. The checklist title.
        items (list): Optional. List of checklist items.

    Returns:
        201: The created checklist as JSON.
        400: If the title field is missing.
    """
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
    """Retrieve all checklists.

    Returns:
        200: A JSON array of all checklists.
    """
    checklist_manager = ChecklistManager(request.db)
    checklists = checklist_manager.get_all_checklists()
    response = [checklist.to_dict() for checklist in checklists]
    return jsonify(response)


@checklists_bp.route("/checklists/<int:checklist_id>", methods=["GET"])
def get_checklist(checklist_id):
    """Retrieve a single checklist by ID.

    Path parameters:
        checklist_id (int): The ID of the checklist.

    Returns:
        200: The checklist as JSON.
        404: If the checklist is not found.
    """
    checklist_manager = ChecklistManager(request.db)
    checklist = checklist_manager.get_checklist(checklist_id)

    if not checklist:
        return jsonify({"error": "Checklist not found"}), 404

    return jsonify(checklist.to_dict())


@checklists_bp.route("/checklists/<int:checklist_id>", methods=["PUT"])
def update_checklist(checklist_id):
    """Update an existing checklist.

    Path parameters:
        checklist_id (int): The ID of the checklist to update.

    Request body (JSON):
        Any checklist fields to update (e.g. title, items).

    Returns:
        200: The updated checklist as JSON.
        400: If no data is provided.
        404: If the checklist is not found.
    """
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
    """Delete a checklist by ID.

    Path parameters:
        checklist_id (int): The ID of the checklist to delete.

    Returns:
        200: A success message confirming deletion.
        404: If the checklist is not found.
    """
    checklist_manager = ChecklistManager(request.db)
    checklist = checklist_manager.delete_checklist(checklist_id)

    if not checklist:
        return jsonify({"error": "Checklist not found"}), 404

    return jsonify({"message": "Checklist deleted successfully"})


@checklists_bp.route("/checklists/<int:checklist_id>/print", methods=["POST"])
def print_checklist(checklist_id):
    """Send a checklist to the printer via the message broker.

    Path parameters:
        checklist_id (int): The ID of the checklist to print.

    Returns:
        200: A status confirmation that the print job was queued.
        404: If the checklist is not found.
    """
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
