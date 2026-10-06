import io
import json
import os
import tempfile
import uuid
from datetime import datetime
from logging import getLogger

from flask import Blueprint, jsonify, request
from flask_sock import Sock

from dashboard.src.storage import get_storage_client

logger = getLogger(__name__)
audio = Blueprint("audio", __name__, url_prefix="/audio")
sock = Sock()

ALLOWED_EXTENSIONS = {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".aac"}


def _generate_remote_filename(
    original_filename: str, fallback_ext: str = ".m4a"
) -> tuple:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    ext = os.path.splitext(original_filename)[1] if original_filename else fallback_ext
    return f"audio/{timestamp}_{unique_id}{ext}", ext


def _upload_to_minio(temp_path: str, remote_filename: str) -> dict:
    url = get_storage_client("minio").upload_file(temp_path, remote_filename)
    logger.info(f"Audio uploaded: {remote_filename}")
    return {"status": "success", "filename": remote_filename, "url": url}


@audio.route("/upload", methods=["POST"])
def upload_audio():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    remote_filename, ext = _generate_remote_filename(file.filename)

    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        file.save(temp_file.name)
        temp_file.close()
        return jsonify(_upload_to_minio(temp_file.name, remote_filename)), 201
    except Exception as e:
        logger.error(f"Failed to upload audio: {e}")
        return jsonify({"error": "Failed to upload file"}), 500
    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


@audio.route("/transcribe", methods=["POST"])
def transcribe_audio():
    data = request.get_json()
    filename = data.get("filename") if data else None
    if not filename:
        return jsonify({"error": "filename is required"}), 400

    try:
        audio_bytes = get_storage_client("minio").read_file(filename, "audio")

        from dashboard.src.ai.clients import get_ai_client

        transcription = get_ai_client("openai").transcribe(
            io.BytesIO(audio_bytes), filename=filename
        )

        return jsonify({"filename": filename, "transcription": transcription})
    except Exception as e:
        logger.error(f"Failed to transcribe {filename}: {e}")
        return jsonify({"error": "Failed to transcribe file"}), 500


@audio.route("/stream", methods=["POST"])
def stream_audio():
    ext = request.args.get("ext", "").lower()
    if not ext.startswith("."):
        ext = f".{ext}" if ext else ""

    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return (
            jsonify({"error": f"Missing or unsupported extension. Allowed: {allowed}"}),
            400,
        )

    if request.content_length is not None and request.content_length == 0:
        return jsonify({"error": "No audio data provided"}), 400

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    remote_filename = f"audio/{timestamp}_{uuid.uuid4().hex[:8]}{ext}"

    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        bytes_written = 0
        while chunk := request.stream.read(8192):
            temp_file.write(chunk)
            bytes_written += len(chunk)
        temp_file.close()

        if bytes_written == 0:
            return jsonify({"error": "No audio data provided"}), 400

        return jsonify(_upload_to_minio(temp_file.name, remote_filename)), 201
    except Exception as e:
        logger.error(f"Failed to upload streamed audio: {e}")
        return jsonify({"error": "Failed to upload file"}), 500
    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def ws_audio(ws):
    """
    WebSocket endpoint for real-time chunked audio streaming.

    Protocol:
        Client -> (optional) JSON text: {"ext": ".mp3"}
        Client -> binary chunk(s)
        Client -> close connection
        Server -> JSON text: {"status": "success", "filename": "...", "url": "..."}
    """
    ext = ".wav"
    chunks = []
    temp_file = None

    try:
        while True:
            data = ws.receive(timeout=30)
            if data is None:
                break

            if isinstance(data, str):
                if not chunks:
                    try:
                        config = json.loads(data)
                    except (json.JSONDecodeError, TypeError):
                        ws.send(json.dumps({"error": "Invalid JSON config"}))
                        return

                    requested_ext = config.get("ext", ".wav")
                    if not requested_ext.startswith("."):
                        requested_ext = f".{requested_ext}"
                    if requested_ext not in ALLOWED_EXTENSIONS:
                        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
                        ws.send(
                            json.dumps(
                                {"error": f"Unsupported extension. Allowed: {allowed}"}
                            )
                        )
                        return
                    ext = requested_ext
            else:
                chunks.append(data)

        if not chunks:
            ws.send(json.dumps({"error": "No audio data received"}))
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        remote_filename = f"audio/{timestamp}_{uuid.uuid4().hex[:8]}{ext}"

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        for chunk in chunks:
            temp_file.write(chunk)
        temp_file.close()

        result = _upload_to_minio(temp_file.name, remote_filename)
        ws.send(json.dumps(result))

    except Exception as e:
        logger.error(f"WebSocket audio error: {e}")
        try:
            ws.send(json.dumps({"error": "Failed to upload file"}))
        except Exception as send_err:
            logger.error(f"WebSocket send error: {send_err}")
    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


sock.route("/audio/ws")(ws_audio)
