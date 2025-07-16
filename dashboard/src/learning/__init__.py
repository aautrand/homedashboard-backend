from flask import Blueprint, request
from sqlalchemy import select

from dashboard.src.learning.models.card import Card

learning = Blueprint("learning", __name__, url_prefix="/learning")


@learning.route("/cards", methods=["GET"])
def get_non_reviewed_cards():
    # Get data from request
    reviewed = request.args.get("reviewed", None)
    if reviewed:
        stmt = select(Card).where(Card.reviewed == reviewed)
    else:
        stmt = select(Card)
    results = request.db.execute(stmt).scalars().all()
    response = [card.to_json() for card in results]
    return response


# TODO Add insert card endpoint
# TODO add review card endpoint
