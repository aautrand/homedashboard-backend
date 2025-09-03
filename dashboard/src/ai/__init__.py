import logging

from flask import Blueprint, jsonify, request

from .clients.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

ai = Blueprint("ai", __name__, url_prefix="/ai")
ollama_client = OllamaClient()


@ai.route("/message", methods=["POST"])
def message():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400

    user_message = data["message"]

    try:
        # Forward message to local LLM
        llm_response = ollama_client.generate_response(user_message)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({"error": "Failed to process message"}), 500

    return jsonify(
        {
            "status": "Message received and processed",
            "user_message": user_message,
            "llm_response": llm_response,
        }
    )
