import hmac
import io
import logging
import os
import tempfile
import uuid
from datetime import datetime
from urllib.parse import unquote_plus

from flask import Blueprint, current_app, jsonify, request

from dashboard.src.storage import get_storage_client

from .agents.home_agent import get_home_agent
from .agents.voice_agent import process_voice_query
from .clients import get_ai_client
from .voice_query_manager import VoiceQueryManager

logger = logging.getLogger(__name__)

ai = Blueprint("ai", __name__, url_prefix="/ai")


@ai.route("/message", methods=["POST"])
def message():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400

    user_message = data["message"]

    try:
        llm_response = get_ai_client("ollama").generate_response(user_message)
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


def _run_voice_query(audio, filename: str) -> dict:
    """Run the voice pipeline with production dependencies for this request."""
    return process_voice_query(
        audio,
        filename,
        transcriber=get_ai_client("openai"),
        agent=get_home_agent(request.db),
        voice_queries=VoiceQueryManager(request.db),
    )


@ai.route("/agent", methods=["POST"])
def agent_message():
    """Send a text request to the home agent. Useful for testing without audio."""
    data = request.get_json(silent=True)
    if not data or not data.get("message"):
        return jsonify({"error": "Message is required"}), 400

    try:
        response = get_home_agent(request.db).respond(data["message"])
    except Exception as e:
        logger.error(f"Agent failed: {e}")
        return jsonify({"error": "Failed to process message"}), 500

    return jsonify({"message": data["message"], "response": response})


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

        with open(temp_file.name, "rb") as audio:
            result = _run_voice_query(audio, remote_filename)

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


def _is_authorized_event() -> bool:
    """Check the bearer token MinIO sends with each notification."""
    token = current_app.config.get("MINIO_EVENT_TOKEN")
    if not token:
        return False
    return hmac.compare_digest(
        request.headers.get("Authorization", ""), f"Bearer {token}"
    )


@ai.route("/audio/events", methods=["POST"])
def audio_events():
    """MinIO bucket notification webhook: answer each newly stored recording.

    Configure MinIO's notify_webhook with auth_token set to MINIO_EVENT_TOKEN.
    Recordings already in voice_queries are skipped, since MinIO may deliver
    the same event more than once.
    """
    if not _is_authorized_event():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    voice_queries = VoiceQueryManager(request.db)
    storage = get_storage_client("minio")
    processed = []

    for record in data.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        # Object keys arrive URL-encoded ("audio%2Fclip.wav").
        filename = unquote_plus(record["s3"]["object"]["key"])

        if voice_queries.is_processed(filename):
            logger.info(f"Skipping already processed recording {filename}")
            continue

        try:
            audio = io.BytesIO(storage.read_file(filename, bucket))
            result = _run_voice_query(audio, filename)
        except Exception as e:
            logger.error(f"Failed to process recording {filename}: {e}")
            return jsonify({"error": "Failed to process audio"}), 500

        processed.append({"filename": filename, **result})

    return jsonify({"status": "ok", "processed": processed})
