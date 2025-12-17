import json
from logging import getLogger

from flask import Blueprint, request

from dashboard.src.message_broker.clients.base import get_message_broker_client
from dashboard.src.prints.print_manager import PrintManager

logger = getLogger(__name__)

prints_bp = Blueprint("prints", __name__)


@prints_bp.route("/print/pop-quiz", methods=["POST"])
def print_pop_quiz():
    logger.info("Printing pop quiz")
    data = request.get_json() or {}
    include_answers = data.get("include_answers", True)

    print_manager = PrintManager()
    pop_quiz, cards, quiz = print_manager.print_pop_quiz()
    rabbit_client = get_message_broker_client()
    rabbit_client.send_message(
        exchange="", routing_key="text_print", body=json.dumps(pop_quiz)
    )
    # Print answers immediately after (if requested)
    if include_answers and cards:
        answers = print_manager.print_pop_quiz_answers(cards)
        rabbit_client.send_message(
            exchange="", routing_key="text_print", body=json.dumps(answers)
        )
    return {"status": "ok", "quiz_id": quiz.id if quiz else None}