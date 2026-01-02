from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from dashboard.src.learning.learning_manager import CardManager
from dashboard.src.learning.models.card import Card
from dashboard.src.learning.models.topic import Topic

cards_bp = Blueprint("cards", __name__)


@cards_bp.route("/cards", methods=["POST"])
def create_card():
    data = request.get_json()

    if not data or "title" not in data or "content" not in data:
        return jsonify({"error": "Missing required fields: title, content"}), 400

    card_manager = CardManager(request.db)
    card = card_manager.add_card(title=data["title"], content=data["content"])

    return jsonify(card.to_dict()), 201


@cards_bp.route("/cards/batch", methods=["POST"])
def create_cards_batch():
    data = request.get_json()

    if not data or not isinstance(data, list):
        return jsonify({"error": "Expected a list of cards"}), 400

    card_manager = CardManager(request.db)
    created_cards = []

    for card_data in data:
        if "title" not in card_data or "content" not in card_data:
            return jsonify({"error": "Each card must have title and content"}), 400

        card = card_manager.add_card(
            title=card_data["title"], content=card_data["content"]
        )
        created_cards.append(card.to_dict())

    return jsonify(created_cards), 201


@cards_bp.route("/cards/<int:card_id>", methods=["PUT"])
def update_card(card_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Extract and validate topic_ids before passing to update_card
    topic_ids = data.pop("topic_ids", None)
    if topic_ids is not None:
        if not isinstance(topic_ids, list):
            return jsonify({"error": "topic_ids must be a list"}), 400
        if not all(isinstance(tid, int) for tid in topic_ids):
            return jsonify({"error": "topic_ids must be a list of integers"}), 400

    card_manager = CardManager(request.db)
    data["reviewed_date"] = datetime.now()
    data["reviewed"] = True
    card = card_manager.update_card(card_id, **data)

    if not card:
        return jsonify({"error": "Card not found"}), 404

    # Handle topic associations if topic_ids provided
    if topic_ids is not None:
        if topic_ids:
            topics = request.db.query(Topic).filter(Topic.id.in_(topic_ids)).all()
            found_ids = {t.id for t in topics}
            missing_ids = set(topic_ids) - found_ids
            if missing_ids:
                return jsonify({"error": f"Topics not found: {sorted(missing_ids)}"}), 404
            card.topics = topics
        else:
            # Empty list clears all topic associations
            card.topics = []
        request.db.commit()

    return jsonify(card.to_dict())


@cards_bp.route("/cards/<int:card_id>", methods=["DELETE"])
def delete_card(card_id):
    card_manager = CardManager(request.db)
    card = card_manager.delete_card(card_id)

    if not card:
        return jsonify({"error": "Card not found"}), 404

    return jsonify({"message": "Card deleted successfully"}), 200


@cards_bp.route("/cards", methods=["GET"])
def get_cards():
    card_manager = CardManager(request.db)
    reviewed = request.args.get("reviewed", None)

    if reviewed is None:
        cards = card_manager.get_all_cards()
    elif reviewed.lower() == "false":
        cards = card_manager.get_non_reviewed_cards()
    elif reviewed.lower() == "true":
        cards = card_manager.get_reviewed_cards()
    else:
        cards = card_manager.get_all_cards()

    return jsonify([card.to_dict() for card in cards])


@cards_bp.route("/problem", methods=["GET"])
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