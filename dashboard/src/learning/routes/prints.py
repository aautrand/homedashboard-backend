from logging import getLogger

from flask import Blueprint, request

from dashboard.src.prints import print_manager

logger = getLogger(__name__)

prints_bp = Blueprint("prints", __name__)


@prints_bp.route("/print/pop-quiz", methods=["POST"])
def print_pop_quiz():
    """
    Print a pop quiz.

    Request body (JSON):
        - num_questions (int, optional): Number of questions to include.
            If not provided, includes all available questions.
        - include_answers (bool, optional): Whether to print answers. Defaults to True.

    Returns:
        JSON with status, quiz_id, question_count, and message.
    """
    logger.info("Printing pop quiz")
    data = request.get_json() or {}

    num_questions = data.get("num_questions")
    include_answers = data.get("include_answers", True)

    result = print_manager.print_pop_quiz(
        db=request.db,
        num_questions=num_questions,
        include_answers=include_answers,
    )

    return result