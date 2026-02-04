from datetime import date

from flask import Blueprint, jsonify, request

from dashboard.src.learning.learning_manager import SubjectManager
from dashboard.src.learning.models.subject import Subject

subjects_bp = Blueprint("subjects", __name__)


@subjects_bp.route("/subjects", methods=["POST"])
def create_subject():
    data = request.get_json()

    if not data or "name" not in data:
        return jsonify({"error": "Missing required field: name"}), 400

    subject_manager = SubjectManager(request.db)
    subject = subject_manager.add_subject(name=data["name"])

    return jsonify(subject.to_dict()), 201


@subjects_bp.route("/subjects", methods=["GET"])
def get_subjects():
    subject_manager = SubjectManager(request.db)

    # Check if filtering by study_active
    study_active = request.args.get("study_active")
    if study_active and study_active.lower() == "true":
        subjects = subject_manager.get_study_subjects()
    else:
        subjects = subject_manager.get_all_subjects()

    response = [subject.to_dict() for subject in subjects]
    return jsonify(response)


@subjects_bp.route("/subjects/<int:subject_id>", methods=["GET"])
def get_subject(subject_id):
    subject_manager = SubjectManager(request.db)
    subject = subject_manager.db.get(Subject, subject_id)

    if not subject:
        return jsonify({"error": "Subject not found"}), 404

    return jsonify(subject.to_dict())


@subjects_bp.route("/subjects/<int:subject_id>", methods=["PUT"])
def update_subject(subject_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    subject_manager = SubjectManager(request.db)
    subject = subject_manager.update_subject(subject_id, **data)

    if not subject:
        return jsonify({"error": "Subject not found"}), 404

    return jsonify(subject.to_dict())


@subjects_bp.route("/subjects/<int:subject_id>/study/enable", methods=["POST"])
def enable_subject_study(subject_id):
    """Enable a subject for spaced repetition study."""
    subject_manager = SubjectManager(request.db)
    subject = subject_manager.update_subject(subject_id, study_active=True)

    if not subject:
        return jsonify({"error": "Subject not found"}), 404

    return jsonify(subject.to_dict())


@subjects_bp.route("/subjects/<int:subject_id>/study/disable", methods=["POST"])
def disable_subject_study(subject_id):
    """Disable a subject for spaced repetition study."""
    subject_manager = SubjectManager(request.db)
    subject = subject_manager.update_subject(subject_id, study_active=False)

    if not subject:
        return jsonify({"error": "Subject not found"}), 404

    return jsonify(subject.to_dict())


@subjects_bp.route("/subjects/study/today", methods=["GET"])
def get_todays_studies():
    """Get subjects that should be studied today based on spaced repetition."""
    subject_manager = SubjectManager(request.db)
    today = date.today()
    subjects = subject_manager.get_subjects_for_study_today(today, max_subjects=1)
    response = [subject.to_dict() for subject in subjects]
    return jsonify(response)
