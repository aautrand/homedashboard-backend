from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from dashboard.src.learning.learning_manager import (
    CardManager,
    SubjectManager,
    TopicManager,
)
from dashboard.src.learning.models.card import Card

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


# TODO Add insert card endpoint
# TODO add review card endpoint
