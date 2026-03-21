import io
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask


@pytest.fixture
def app():
    """Create a Flask application for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


class TestAudioUploadEndpoint:
    """Tests for the /audio/upload endpoint."""

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_success(self, mock_get_storage_client, app):
        """Test successful audio file upload."""
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "test_audio.mp3")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data["status"] == "success"
        assert "filename" in json_data
        assert "url" in json_data
        assert json_data["filename"].startswith("audio/")
        assert json_data["filename"].endswith(".mp3")

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_no_file_provided(self, mock_get_storage_client, app):
        """Test upload returns 400 when no file field is provided."""
        from dashboard.src.audio import audio

        app.register_blueprint(audio)

        with app.test_client() as client:
            response = client.post(
                "/audio/upload", data={}, content_type="multipart/form-data"
            )

        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data["error"] == "No file provided"

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_empty_filename(self, mock_get_storage_client, app):
        """Test upload returns 400 when filename is empty."""
        from dashboard.src.audio import audio

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data["error"] == "No file selected"

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_storage_error(self, mock_get_storage_client, app):
        """Test upload returns 500 when storage upload fails."""
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.side_effect = Exception("Storage connection failed")
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "test.mp3")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 500
        json_data = response.get_json()
        assert json_data["error"] == "Failed to upload file"

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_m4a_extension(self, mock_get_storage_client, app):
        """Test upload with .m4a file extension."""
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.m4a"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "voice_memo.m4a")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data["filename"].endswith(".m4a")

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_wav_extension(self, mock_get_storage_client, app):
        """Test upload with .wav file extension."""
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.wav"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "recording.wav")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data["filename"].endswith(".wav")

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_ogg_extension(self, mock_get_storage_client, app):
        """Test upload with .ogg file extension."""
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.ogg"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "podcast.ogg")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data["filename"].endswith(".ogg")

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_filename_format(self, mock_get_storage_client, app):
        """Test uploaded filename has correct format: audio/YYYYMMDD_HHMMSS_uniqueid.ext"""
        import re

        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "test.mp3")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        json_data = response.get_json()
        filename = json_data["filename"]

        pattern = r"^audio/\d{8}_\d{6}_[a-f0-9]{8}\.mp3$"
        assert re.match(pattern, filename), f"Filename {filename} doesn't match expected pattern"

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_storage_client_called_correctly(self, mock_get_storage_client, app):
        """Test storage client is called with correct arguments."""
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "test.mp3")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        mock_get_storage_client.assert_called_once_with("minio")
        assert mock_storage.upload_file.called
        call_args = mock_storage.upload_file.call_args
        assert call_args[0][1].startswith("audio/")
        assert call_args[0][1].endswith(".mp3")

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_get_method_not_allowed(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio
        app.register_blueprint(audio)
        with app.test_client() as client:
            response = client.get("/audio/upload")
        assert response.status_code == 405

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_put_method_not_allowed(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio
        app.register_blueprint(audio)
        with app.test_client() as client:
            response = client.put("/audio/upload")
        assert response.status_code == 405

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_delete_method_not_allowed(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio
        app.register_blueprint(audio)
        with app.test_client() as client:
            response = client.delete("/audio/upload")
        assert response.status_code == 405

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_response_contains_all_fields(self, mock_get_storage_client, app):
        """Test success response contains exactly status, filename, and url."""
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "test.mp3")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        json_data = response.get_json()
        assert set(json_data.keys()) == {"status", "filename", "url"}

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_with_special_characters_in_filename(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "my file (1).mp3")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 201
        assert response.get_json()["filename"].endswith(".mp3")

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_with_unicode_filename(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "音声ファイル.mp3")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 201
        assert response.get_json()["filename"].endswith(".mp3")

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_with_multiple_dots_in_filename(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "my.audio.file.2024.mp3")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 201
        assert response.get_json()["filename"].endswith(".mp3")

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_flac_extension(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.flac"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "lossless.flac")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 201
        assert response.get_json()["filename"].endswith(".flac")

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_aac_extension(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.aac"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "audio.aac")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 201
        assert response.get_json()["filename"].endswith(".aac")

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_url_from_storage_returned(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio

        expected_url = "http://minio-server:9000/my-bucket/audio/20240101_120000_abc12345.mp3"
        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = expected_url
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "test.mp3")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.get_json()["url"] == expected_url

    @patch("dashboard.src.audio.get_storage_client")
    @patch("dashboard.src.audio.os.path.exists")
    @patch("dashboard.src.audio.os.unlink")
    def test_upload_audio_temp_file_cleanup_on_success(
        self, mock_unlink, mock_exists, mock_get_storage_client, app
    ):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage
        mock_exists.return_value = True

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "test.mp3")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 201
        assert mock_unlink.called

    @patch("dashboard.src.audio.get_storage_client")
    @patch("dashboard.src.audio.os.path.exists")
    @patch("dashboard.src.audio.os.unlink")
    def test_upload_audio_temp_file_cleanup_on_error(
        self, mock_unlink, mock_exists, mock_get_storage_client, app
    ):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.side_effect = Exception("Upload failed")
        mock_get_storage_client.return_value = mock_storage
        mock_exists.return_value = True

        app.register_blueprint(audio)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio content"), "test.mp3")}
            response = client.post(
                "/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 500
        assert mock_unlink.called

    @patch("dashboard.src.audio.get_storage_client")
    def test_upload_audio_unique_filenames(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        filenames = []
        with app.test_client() as client:
            for _ in range(5):
                data = {"file": (io.BytesIO(b"fake audio content"), "test.mp3")}
                response = client.post(
                    "/audio/upload", data=data, content_type="multipart/form-data"
                )
                filenames.append(response.get_json()["filename"])

        assert len(filenames) == len(set(filenames))


class TestAudioStreamEndpoint:
    """Tests for the /audio/stream endpoint."""

    @patch("dashboard.src.audio.get_storage_client")
    def test_stream_audio_success(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            response = client.post(
                "/audio/stream?ext=.mp3",
                data=b"fake audio content",
                content_type="application/octet-stream",
            )

        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data["status"] == "success"
        assert json_data["filename"].startswith("audio/")
        assert json_data["filename"].endswith(".mp3")
        assert "url" in json_data

    @patch("dashboard.src.audio.get_storage_client")
    def test_stream_audio_ext_without_dot(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.wav"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            response = client.post(
                "/audio/stream?ext=wav",
                data=b"fake audio content",
                content_type="application/octet-stream",
            )

        assert response.status_code == 201
        assert response.get_json()["filename"].endswith(".wav")

    @patch("dashboard.src.audio.get_storage_client")
    def test_stream_audio_missing_ext(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio
        app.register_blueprint(audio)
        with app.test_client() as client:
            response = client.post(
                "/audio/stream",
                data=b"fake audio content",
                content_type="application/octet-stream",
            )
        assert response.status_code == 400
        assert "extension" in response.get_json()["error"].lower()

    @patch("dashboard.src.audio.get_storage_client")
    def test_stream_audio_unsupported_ext(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio
        app.register_blueprint(audio)
        with app.test_client() as client:
            response = client.post(
                "/audio/stream?ext=.exe",
                data=b"fake audio content",
                content_type="application/octet-stream",
            )
        assert response.status_code == 400

    @patch("dashboard.src.audio.get_storage_client")
    def test_stream_audio_empty_body(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio
        app.register_blueprint(audio)
        with app.test_client() as client:
            response = client.post(
                "/audio/stream?ext=.mp3",
                data=b"",
                content_type="application/octet-stream",
            )
        assert response.status_code == 400
        assert "no audio data" in response.get_json()["error"].lower()

    @patch("dashboard.src.audio.get_storage_client")
    def test_stream_audio_storage_error(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.side_effect = Exception("Storage connection failed")
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            response = client.post(
                "/audio/stream?ext=.mp3",
                data=b"fake audio content",
                content_type="application/octet-stream",
            )

        assert response.status_code == 500
        assert response.get_json()["error"] == "Failed to upload file"

    @patch("dashboard.src.audio.get_storage_client")
    def test_stream_audio_all_extensions(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        for ext in [".mp3", ".m4a", ".wav", ".ogg", ".flac", ".aac"]:
            with app.test_client() as client:
                response = client.post(
                    f"/audio/stream?ext={ext}",
                    data=b"fake audio content",
                    content_type="application/octet-stream",
                )
            assert response.status_code == 201, f"Failed for extension {ext}"

    @patch("dashboard.src.audio.get_storage_client")
    @patch("dashboard.src.audio.os.path.exists")
    @patch("dashboard.src.audio.os.unlink")
    def test_stream_audio_temp_file_cleanup(
        self, mock_unlink, mock_exists, mock_get_storage_client, app
    ):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage
        mock_exists.return_value = True

        app.register_blueprint(audio)

        with app.test_client() as client:
            response = client.post(
                "/audio/stream?ext=.mp3",
                data=b"fake audio content",
                content_type="application/octet-stream",
            )

        assert response.status_code == 201
        assert mock_unlink.called

    @patch("dashboard.src.audio.get_storage_client")
    def test_stream_audio_get_method_not_allowed(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio
        app.register_blueprint(audio)
        with app.test_client() as client:
            response = client.get("/audio/stream?ext=.mp3")
        assert response.status_code == 405

    @patch("dashboard.src.audio.get_storage_client")
    def test_stream_audio_response_contains_all_fields(self, mock_get_storage_client, app):
        from dashboard.src.audio import audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage

        app.register_blueprint(audio)

        with app.test_client() as client:
            response = client.post(
                "/audio/stream?ext=.mp3",
                data=b"fake audio content",
                content_type="application/octet-stream",
            )

        json_data = response.get_json()
        assert set(json_data.keys()) == {"status", "filename", "url"}


class TestAudioBlueprintRegistration:
    def test_blueprint_has_correct_url_prefix(self):
        from dashboard.src.audio import audio
        assert audio.url_prefix == "/audio"

    def test_blueprint_has_correct_name(self):
        from dashboard.src.audio import audio
        assert audio.name == "audio"


class TestWebSocketAudioEndpoint:
    """Tests for the /audio/ws WebSocket endpoint."""

    @patch("dashboard.src.audio.get_storage_client")
    def test_ws_audio_binary_only_defaults_to_wav(self, mock_get_storage_client):
        from dashboard.src.audio import ws_audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.wav"
        mock_get_storage_client.return_value = mock_storage

        mock_ws = MagicMock()
        mock_ws.receive = MagicMock(side_effect=[b"chunk1", b"chunk2", None])

        ws_audio(mock_ws)

        mock_ws.send.assert_called_once()
        response = json.loads(mock_ws.send.call_args[0][0])
        assert response["status"] == "success"
        assert response["filename"].endswith(".wav")
        assert "url" in response

    @patch("dashboard.src.audio.get_storage_client")
    def test_ws_audio_config_with_mp3_extension(self, mock_get_storage_client):
        from dashboard.src.audio import ws_audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.mp3"
        mock_get_storage_client.return_value = mock_storage

        mock_ws = MagicMock()
        mock_ws.receive = MagicMock(
            side_effect=[json.dumps({"ext": ".mp3"}), b"audio data", None]
        )

        ws_audio(mock_ws)

        mock_ws.send.assert_called_once()
        response = json.loads(mock_ws.send.call_args[0][0])
        assert response["status"] == "success"
        assert response["filename"].endswith(".mp3")

    @patch("dashboard.src.audio.get_storage_client")
    def test_ws_audio_unsupported_extension(self, mock_get_storage_client):
        from dashboard.src.audio import ws_audio

        mock_ws = MagicMock()
        mock_ws.receive = MagicMock(
            side_effect=[json.dumps({"ext": ".exe"}), b"audio data", None]
        )

        ws_audio(mock_ws)

        mock_ws.send.assert_called_once()
        response = json.loads(mock_ws.send.call_args[0][0])
        assert "error" in response
        assert "Unsupported extension" in response["error"]

    @patch("dashboard.src.audio.get_storage_client")
    def test_ws_audio_invalid_json_config(self, mock_get_storage_client):
        from dashboard.src.audio import ws_audio

        mock_ws = MagicMock()
        mock_ws.receive = MagicMock(side_effect=["not valid json{{{", b"audio data", None])

        ws_audio(mock_ws)

        mock_ws.send.assert_called_once()
        response = json.loads(mock_ws.send.call_args[0][0])
        assert "error" in response
        assert "Invalid JSON" in response["error"]

    @patch("dashboard.src.audio.get_storage_client")
    def test_ws_audio_no_audio_data(self, mock_get_storage_client):
        from dashboard.src.audio import ws_audio

        mock_ws = MagicMock()
        mock_ws.receive = MagicMock(side_effect=[None])

        ws_audio(mock_ws)

        mock_ws.send.assert_called_once()
        response = json.loads(mock_ws.send.call_args[0][0])
        assert "error" in response
        assert "No audio data" in response["error"]

    @patch("dashboard.src.audio.get_storage_client")
    def test_ws_audio_storage_error(self, mock_get_storage_client):
        from dashboard.src.audio import ws_audio

        mock_storage = MagicMock()
        mock_storage.upload_file.side_effect = Exception("Storage failed")
        mock_get_storage_client.return_value = mock_storage

        mock_ws = MagicMock()
        mock_ws.receive = MagicMock(side_effect=[b"audio data", None])

        ws_audio(mock_ws)

        mock_ws.send.assert_called_once()
        response = json.loads(mock_ws.send.call_args[0][0])
        assert "error" in response
        assert "Failed to upload file" in response["error"]

    @patch("dashboard.src.audio.os.unlink")
    @patch("dashboard.src.audio.os.path.exists")
    @patch("dashboard.src.audio.get_storage_client")
    def test_ws_audio_temp_file_cleanup(self, mock_get_storage_client, mock_exists, mock_unlink):
        from dashboard.src.audio import ws_audio

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = "http://minio:9000/bucket/audio/test.wav"
        mock_get_storage_client.return_value = mock_storage
        mock_exists.return_value = True

        mock_ws = MagicMock()
        mock_ws.receive = MagicMock(side_effect=[b"audio data", None])

        ws_audio(mock_ws)

        assert mock_unlink.called
