from logging import getLogger

from flask import Blueprint, request

from dashboard.src.prints import orchestration

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

    result = orchestration.print_pop_quiz(
        db=request.db,
        num_questions=num_questions,
        include_answers=include_answers,
    )

    return result


@prints_bp.route("/print/quiz/<int:quiz_id>", methods=["POST"])
def reprint_quiz(quiz_id: int):
    """
    Reprint a previously generated quiz.

    Args:
        quiz_id: ID of the quiz (from URL path)

    Request body (JSON, optional):
        - include_answers (bool, optional): Whether to print answers. Defaults to True.
        - randomize (bool, optional): Whether to randomize question order. Defaults to True.

    Returns:
        JSON with status, quiz_id, question_count, and message.
    """
    logger.info(f"Reprinting quiz #{quiz_id}")
    data = request.get_json() or {}
    include_answers = data.get("include_answers", True)
    randomize = data.get("randomize", True)

    result = orchestration.reprint_quiz(
        db=request.db,
        quiz_id=quiz_id,
        include_answers=include_answers,
        randomize=randomize,
    )

    return result


@prints_bp.route("/print/quiz/<int:quiz_id>/answers", methods=["POST"])
def print_quiz_answers(quiz_id: int):
    """
    Print the answers for a specific quiz.

    Args:
        quiz_id: ID of the quiz (from URL path)

    Returns:
        JSON with status, quiz_id, question_count, and message.
    """
    logger.info(f"Printing answers for quiz #{quiz_id}")

    result = orchestration.print_quiz_answers(
        db=request.db,
        quiz_id=quiz_id,
    )

    return result


@prints_bp.route("/quiz", methods=["GET"])
def get_quizzes():
    """
    Get all quizzes, ordered by creation date (newest first).

    Returns:
        JSON list of quizzes with id, created_date, and question_count.
    """
    from dashboard.src.learning.learning_manager import QuizManager

    quiz_manager = QuizManager(request.db)
    quizzes = quiz_manager.get_all_quizzes()

    return [
        {
            "id": quiz.id,
            "created_date": quiz.created_date.isoformat(),
            "question_count": len(quiz.questions),
        }
        for quiz in quizzes
    ]
