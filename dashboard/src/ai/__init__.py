import logging
import os
import tempfile
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request

from dashboard.src.storage import get_storage_client

from .agents.voice_agent import process_voice_query
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


@ai.route("/audio/upload", methods=["POST"])
def upload_audio():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    ext = os.path.splitext(file.filename)[1] if file.filename else ".m4a"
    remote_filename = f"audio/{timestamp}_{unique_id}{ext}"

    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        file.save(temp_file.name)
        temp_file.close()

        url = get_storage_client("minio").upload_file(temp_file.name, remote_filename)

        result = process_voice_query(temp_file.name, remote_filename, request.db)

        return (
            jsonify(
                {"status": "success", "filename": remote_filename, "url": url, **result}
            ),
            201,
        )
    except Exception as e:
        logger.error(f"Failed to process audio upload: {e}")
        return jsonify({"error": "Failed to process audio"}), 500
    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
