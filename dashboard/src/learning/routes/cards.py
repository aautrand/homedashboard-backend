from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from dashboard.src.learning.learning_manager import CardManager
from dashboard.src.learning.models.card import Card

cards_bp = Blueprint("cards", __name__)


@cards_bp.route("/cards/<int:card_id>", methods=["PUT"])
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


@cards_bp.route("/cards", methods=["GET"])
def get_cards():
    card_manager = CardManager(request.db)
    reviewed = request.args.get("reviewed", None)

    if reviewed and reviewed.lower() == "false":
        cards = card_manager.get_non_reviewed_cards()
    else:
        cards = card_manager.get_all_cards()

    response = [card.to_json() for card in cards]
    return response


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