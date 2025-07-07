import logging

from flask import Blueprint, request

logger = logging.getLogger(__name__)

ai = Blueprint("ai", __name__, url_prefix="/ai")


@ai.route("/card", methods=["POST"])
def add_card():
    logger.info("Adding new card.")
    body = request.get_json()
    data = body["prompt"]
    logger.info(data)
    return {"status": "Card Added"}
