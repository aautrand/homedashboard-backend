from flask import Blueprint, jsonify, request

from dashboard.src.learning.learning_manager import TopicManager

topics_bp = Blueprint("topics", __name__)


@topics_bp.route("/topics", methods=["GET"])
def get_topics():
    topic_manager = TopicManager(request.db)
    topics = topic_manager.get_all_topics()

    return jsonify(
        [
            {
                "id": topic.id,
                "name": topic.name,
                "subject_id": topic.subject_id,
                "parent_topic_id": topic.parent_topic_id,
            }
            for topic in topics
        ]
    )


@topics_bp.route("/topics", methods=["POST"])
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
