from logging import getLogger

from flask import Blueprint, request, jsonify

from dashboard.src.learning.learning_manager import QuizManager

logger = getLogger(__name__)

quizzes_bp = Blueprint("quizzes", __name__)


@quizzes_bp.route("/quiz/<int:quiz_id>/question/<int:question_id>/answer", methods=["POST"])
def record_answer(quiz_id: int, question_id: int):
    """
    Record an answer for a single quiz question.

    Args:
        quiz_id: ID of the quiz (from URL path)
        question_id: ID of the quiz question (from URL path)

    Request body (JSON):
        - score (int, required): 0=incorrect, 1=partial, 2=correct

    Returns:
        JSON with the recorded answer details.
    """
    data = request.get_json()
    if not data or "score" not in data:
        return jsonify({"error": "score is required"}), 400

    score = data["score"]
    if score not in (0, 1, 2):
        return jsonify({"error": "score must be 0, 1, or 2"}), 400

    quiz_manager = QuizManager(request.db)

    # Verify the question belongs to the quiz
    questions = quiz_manager.get_quiz_questions(quiz_id)
    question = next((q for q in questions if q.id == question_id), None)

    if not question:
        return jsonify({"error": "Question not found in this quiz"}), 404

    answer = quiz_manager.record_answer(question_id, score)

    logger.info(f"Recorded answer for quiz {quiz_id}, question {question_id}: score={score}")

    return jsonify({
        "id": answer.id,
        "quiz_question_id": answer.quiz_question_id,
        "score": answer.score,
        "score_label": answer.score_label,
        "created_date": answer.created_date.isoformat(),
    }), 201


@quizzes_bp.route("/quiz/<int:quiz_id>/answers", methods=["POST"])
def record_answers_bulk(quiz_id: int):
    """
    Record answers for multiple questions in a quiz at once.

    Args:
        quiz_id: ID of the quiz (from URL path)

    Request body (JSON):
        - answers (list, required): List of answer objects, each with:
            - question_id (int): ID of the quiz question
            - score (int): 0=incorrect, 1=partial, 2=correct

    Example:
        {
            "answers": [
                {"question_id": 1, "score": 2},
                {"question_id": 2, "score": 1},
                {"question_id": 3, "score": 0}
            ]
        }

    Returns:
        JSON with summary and list of recorded answers.
    """
    data = request.get_json()
    if not data or "answers" not in data:
        return jsonify({"error": "answers list is required"}), 400

    answers_input = data["answers"]
    if not isinstance(answers_input, list):
        return jsonify({"error": "answers must be a list"}), 400

    quiz_manager = QuizManager(request.db)

    # Get all questions for this quiz to validate
    questions = quiz_manager.get_quiz_questions(quiz_id)
    question_ids = {q.id for q in questions}

    if not questions:
        return jsonify({"error": "Quiz not found or has no questions"}), 404

    # Validate all answers before recording any
    for ans in answers_input:
        if "question_id" not in ans or "score" not in ans:
            return jsonify({"error": "Each answer must have question_id and score"}), 400
        if ans["question_id"] not in question_ids:
            return jsonify({"error": f"Question {ans['question_id']} not found in quiz {quiz_id}"}), 404
        if ans["score"] not in (0, 1, 2):
            return jsonify({"error": f"Invalid score {ans['score']} for question {ans['question_id']}"}), 400

    # Record all answers
    recorded = []
    for ans in answers_input:
        answer = quiz_manager.record_answer(ans["question_id"], ans["score"])
        recorded.append({
            "id": answer.id,
            "quiz_question_id": answer.quiz_question_id,
            "score": answer.score,
            "score_label": answer.score_label,
            "created_date": answer.created_date.isoformat(),
        })

    logger.info(f"Recorded {len(recorded)} answers for quiz {quiz_id}")

    return jsonify({
        "quiz_id": quiz_id,
        "answers_recorded": len(recorded),
        "answers": recorded,
    }), 201


@quizzes_bp.route("/quiz/<int:quiz_id>", methods=["GET"])
def get_quiz(quiz_id: int):
    """
    Get a quiz with its questions and cards.

    Args:
        quiz_id: ID of the quiz (from URL path)

    Returns:
        JSON with quiz details including questions and their cards.
    """
    quiz_manager = QuizManager(request.db)
    questions = quiz_manager.get_quiz_questions(quiz_id)

    if not questions:
        return jsonify({"error": "Quiz not found"}), 404

    quiz = questions[0].quiz

    return jsonify({
        "id": quiz.id,
        "created_date": quiz.created_date.isoformat(),
        "questions": [
            {
                "id": q.id,
                "position": q.position,
                "card": {
                    "id": q.card.id,
                    "title": q.card.title,
                    "content": q.card.content,
                },
                "answers": [
                    {
                        "id": a.id,
                        "score": a.score,
                        "score_label": a.score_label,
                        "created_date": a.created_date.isoformat(),
                    }
                    for a in q.answers
                ],
            }
            for q in questions
        ],
    })