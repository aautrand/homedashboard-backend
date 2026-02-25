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


@audio.route("/upload", methods=["POST"])
def upload_audio():
    """
    Accept an audio file upload and store it in MinIO.

    Expected: multipart/form-data with 'file' field containing the audio file.

    Returns:
        JSON with upload status and file URL.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Generate a unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    original_ext = os.path.splitext(file.filename)[1] if file.filename else ".m4a"
    remote_filename = f"audio/{timestamp}_{unique_id}{original_ext}"

    # Save to temp file, upload to MinIO, then clean up
    temp_file = None
    try:
        # Create temp file with the same extension
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=original_ext)
        file.save(temp_file.name)
        temp_file.close()

        # Upload to MinIO
        storage_client = get_storage_client("minio")
        url = storage_client.upload_file(temp_file.name, remote_filename)

        logger.info(f"Audio file uploaded: {remote_filename}")

        return (
            jsonify({"status": "success", "filename": remote_filename, "url": url}),
            201,
        )

    except Exception as e:
        logger.error(f"Failed to upload audio file: {e}")
        return jsonify({"error": "Failed to upload file"}), 500

    finally:
        # Clean up temp file
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


@audio.route("/stream", methods=["POST"])
def stream_audio():
    """
    Accept a streamed audio file via raw request body and store it in MinIO.

    The file extension must be provided via the 'ext' query parameter
    (e.g. ?ext=.mp3). The raw audio bytes are read from the request body.

    Returns:
        JSON with upload status and file URL.
    """
    ext = request.args.get("ext", "").lower()
    if not ext.startswith("."):
        ext = f".{ext}" if ext else ""

    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return jsonify({"error": f"Missing or unsupported extension. Allowed: {allowed}"}), 400

    if request.content_length is not None and request.content_length == 0:
        return jsonify({"error": "No audio data provided"}), 400

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    remote_filename = f"audio/{timestamp}_{unique_id}{ext}"

    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)

        # Stream chunks from the request body to the temp file
        chunk_size = 8192
        bytes_written = 0
        while True:
            chunk = request.stream.read(chunk_size)
            if not chunk:
                break
            temp_file.write(chunk)
            bytes_written += len(chunk)
        temp_file.close()

        if bytes_written == 0:
            return jsonify({"error": "No audio data provided"}), 400

        storage_client = get_storage_client("minio")
        url = storage_client.upload_file(temp_file.name, remote_filename)

        logger.info(f"Streamed audio file uploaded: {remote_filename} ({bytes_written} bytes)")

        return (
            jsonify({"status": "success", "filename": remote_filename, "url": url}),
            201,
        )

    except Exception as e:
        logger.error(f"Failed to upload streamed audio file: {e}")
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
                # First text message is config
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

        # Write chunks to temp file and upload
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        remote_filename = f"audio/{timestamp}_{unique_id}{ext}"

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        for chunk in chunks:
            temp_file.write(chunk)
        temp_file.close()

        storage_client = get_storage_client("minio")
        url = storage_client.upload_file(temp_file.name, remote_filename)

        logger.info(f"WebSocket audio uploaded: {remote_filename}")

        ws.send(
            json.dumps({"status": "success", "filename": remote_filename, "url": url})
        )

    except Exception as e:
        logger.error(f"WebSocket audio error: {e}")
        try:
            ws.send(json.dumps({"error": "Failed to upload file"}))
        except Exception:
            pass

    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


sock.route("/audio/ws")(ws_audio)
