import os
import tempfile
import uuid
from datetime import datetime
from logging import getLogger

from flask import Blueprint, jsonify, request

from dashboard.src.storage import get_storage_client

logger = getLogger(__name__)
audio = Blueprint("audio", __name__, url_prefix="/audio")


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
