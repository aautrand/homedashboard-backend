from unittest.mock import MagicMock, patch

import pytest
from flask import Flask


@pytest.fixture
def app():
    """Create a Flask application for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    with patch("dashboard.src.ai.get_ai_client"):
        from dashboard.src.ai import ai

        app.register_blueprint(ai)
        with app.test_client() as client:
            yield client


class TestAIBlueprint:
    """Tests for the AI Blueprint endpoints."""

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_success(self, mock_get_ai_client, app):
        """Test /ai/message endpoint returns success response."""
        from dashboard.src.ai import ai

        mock_get_ai_client.return_value.generate_response.return_value = (
            "Hello! I can help you."
        )

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/message",
                json={"message": "Hello"},
                content_type="application/json",
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "Message received and processed"
        assert data["user_message"] == "Hello"
        assert data["llm_response"] == "Hello! I can help you."

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_missing_message_field(self, mock_get_ai_client, app):
        """Test /ai/message endpoint returns 400 when message field is missing."""
        from dashboard.src.ai import ai

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/message",
                json={"wrong_field": "test"},
                content_type="application/json",
            )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Message is required"

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_empty_json(self, mock_get_ai_client, app):
        """Test /ai/message endpoint returns 400 for empty JSON body."""
        from dashboard.src.ai import ai

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/message", json={}, content_type="application/json"
            )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "Message is required"

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_no_json_body(self, mock_get_ai_client, app):
        """Test /ai/message endpoint returns 400 for missing JSON body."""
        from dashboard.src.ai import ai

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post("/ai/message", content_type="application/json")

        assert response.status_code == 400

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_ollama_error(self, mock_get_ai_client, app):
        """Test /ai/message endpoint returns 500 on Ollama error."""
        from dashboard.src.ai import ai

        mock_get_ai_client.return_value.generate_response.side_effect = Exception(
            "Ollama service unavailable"
        )

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/message",
                json={"message": "Hello"},
                content_type="application/json",
            )

        assert response.status_code == 500
        data = response.get_json()
        assert data["error"] == "Failed to process message"

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_with_long_message(self, mock_get_ai_client, app):
        """Test /ai/message endpoint handles long messages."""
        from dashboard.src.ai import ai

        long_message = "Tell me about " + "science " * 500
        mock_get_ai_client.return_value.generate_response.return_value = (
            "Here's the information..."
        )

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/message",
                json={"message": long_message},
                content_type="application/json",
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user_message"] == long_message

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_with_special_characters(self, mock_get_ai_client, app):
        """Test /ai/message endpoint handles special characters."""
        from dashboard.src.ai import ai

        special_message = "Code: print('Hello <World>') & test=\"value\""
        mock_get_ai_client.return_value.generate_response.return_value = (
            "I see code with special chars."
        )

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/message",
                json={"message": special_message},
                content_type="application/json",
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user_message"] == special_message

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_with_unicode(self, mock_get_ai_client, app):
        """Test /ai/message endpoint handles unicode characters."""
        from dashboard.src.ai import ai

        unicode_message = "你好世界 🌍 café résumé"
        mock_get_ai_client.return_value.generate_response.return_value = (
            "Hello in Chinese and more!"
        )

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/message",
                json={"message": unicode_message},
                content_type="application/json",
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user_message"] == unicode_message

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_response_format(self, mock_get_ai_client, app):
        """Test /ai/message endpoint response has correct structure."""
        from dashboard.src.ai import ai

        mock_get_ai_client.return_value.generate_response.return_value = "Response"

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/message", json={"message": "Test"}, content_type="application/json"
            )

        data = response.get_json()

        # Verify all expected fields are present
        assert "status" in data
        assert "user_message" in data
        assert "llm_response" in data

        # Verify no unexpected fields
        assert len(data) == 3

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_get_method_not_allowed(self, mock_get_ai_client, app):
        """Test /ai/message endpoint rejects GET requests."""
        from dashboard.src.ai import ai

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.get("/ai/message")

        assert response.status_code == 405

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_with_empty_message(self, mock_get_ai_client, app):
        """Test /ai/message endpoint handles empty message string."""
        from dashboard.src.ai import ai

        mock_get_ai_client.return_value.generate_response.return_value = ""

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/message", json={"message": ""}, content_type="application/json"
            )

        # Empty string is still a valid message value
        assert response.status_code == 200

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_with_whitespace_message(self, mock_get_ai_client, app):
        """Test /ai/message endpoint handles whitespace-only message."""
        from dashboard.src.ai import ai

        mock_get_ai_client.return_value.generate_response.return_value = (
            "You sent whitespace"
        )

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/message", json={"message": "   "}, content_type="application/json"
            )

        assert response.status_code == 200

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_extra_fields_ignored(self, mock_get_ai_client, app):
        """Test /ai/message endpoint ignores extra fields in request."""
        from dashboard.src.ai import ai

        mock_get_ai_client.return_value.generate_response.return_value = "Response"

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/message",
                json={"message": "Hello", "extra_field": "ignored", "another": 123},
                content_type="application/json",
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["user_message"] == "Hello"

    @patch("dashboard.src.ai.get_ai_client")
    def test_message_endpoint_timeout_error(self, mock_get_ai_client, app):
        """Test /ai/message endpoint handles timeout errors."""
        from dashboard.src.ai import ai

        mock_get_ai_client.return_value.generate_response.side_effect = Exception(
            "Connection timed out"
        )

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/message",
                json={"message": "Hello"},
                content_type="application/json",
            )

        assert response.status_code == 500
        data = response.get_json()
        assert data["error"] == "Failed to process message"


class TestAIBlueprintRegistration:
    """Tests for AI Blueprint registration."""

    def test_blueprint_has_correct_url_prefix(self):
        """Test AI blueprint has /ai URL prefix."""
        from dashboard.src.ai import ai

        assert ai.url_prefix == "/ai"

    def test_blueprint_has_correct_name(self):
        """Test AI blueprint has correct name."""
        from dashboard.src.ai import ai

        assert ai.name == "ai"


class TestAIAudioUploadEndpoint:
    """Tests for the /ai/audio/upload endpoint."""

    @patch("dashboard.src.ai.get_receipt_printer")
    @patch("dashboard.src.ai.get_home_agent")
    @patch("dashboard.src.ai.get_ai_client")
    @patch("dashboard.src.ai.process_voice_query")
    @patch("dashboard.src.ai.get_storage_client")
    def test_upload_success(
        self,
        mock_get_storage_client,
        mock_process_voice_query,
        mock_get_ai_client,
        mock_get_home_agent,
        mock_get_receipt_printer,
        app,
    ):
        import io

        from dashboard.src.ai import ai

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = (
            "http://minio:9000/bucket/audio/test.m4a"
        )
        mock_get_storage_client.return_value = mock_storage
        mock_process_voice_query.return_value = {
            "transcription": "hello",
            "llm_response": "world",
        }

        mock_db = MagicMock()
        app.register_blueprint(ai)

        @app.before_request
        def inject_db():
            from flask import request

            request.db = mock_db

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio"), "voice.m4a")}
            response = client.post(
                "/ai/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data["status"] == "success"
        assert "filename" in json_data
        assert "url" in json_data
        assert json_data["transcription"] == "hello"
        assert json_data["llm_response"] == "world"

    def test_upload_no_file(self, app):
        from dashboard.src.ai import ai

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.post(
                "/ai/audio/upload", data={}, content_type="multipart/form-data"
            )

        assert response.status_code == 400
        assert response.get_json()["error"] == "No file provided"

    def test_upload_empty_filename(self, app):
        import io

        from dashboard.src.ai import ai

        app.register_blueprint(ai)

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio"), "")}
            response = client.post(
                "/ai/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 400
        assert response.get_json()["error"] == "No file selected"

    @patch("dashboard.src.ai.get_storage_client")
    def test_upload_storage_error(self, mock_get_storage_client, app):
        import io

        from dashboard.src.ai import ai

        mock_storage = MagicMock()
        mock_storage.upload_file.side_effect = Exception("Storage failed")
        mock_get_storage_client.return_value = mock_storage

        mock_db = MagicMock()
        app.register_blueprint(ai)

        @app.before_request
        def inject_db():
            from flask import request

            request.db = mock_db

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio"), "voice.m4a")}
            response = client.post(
                "/ai/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 500
        assert response.get_json()["error"] == "Failed to process audio"

    @patch("dashboard.src.ai.get_receipt_printer")
    @patch("dashboard.src.ai.get_home_agent")
    @patch("dashboard.src.ai.get_ai_client")
    @patch("dashboard.src.ai.process_voice_query")
    @patch("dashboard.src.ai.get_storage_client")
    def test_upload_voice_query_error(
        self,
        mock_get_storage_client,
        mock_process_voice_query,
        mock_get_ai_client,
        mock_get_home_agent,
        mock_get_receipt_printer,
        app,
    ):
        import io

        from dashboard.src.ai import ai

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = (
            "http://minio:9000/bucket/audio/test.m4a"
        )
        mock_get_storage_client.return_value = mock_storage
        mock_process_voice_query.side_effect = Exception("Voice query failed")

        mock_db = MagicMock()
        app.register_blueprint(ai)

        @app.before_request
        def inject_db():
            from flask import request

            request.db = mock_db

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio"), "voice.m4a")}
            response = client.post(
                "/ai/audio/upload", data=data, content_type="multipart/form-data"
            )

        assert response.status_code == 500
        assert response.get_json()["error"] == "Failed to process audio"

    @patch("dashboard.src.ai.get_receipt_printer")
    @patch("dashboard.src.ai.get_home_agent")
    @patch("dashboard.src.ai.get_ai_client")
    @patch("dashboard.src.ai.process_voice_query")
    @patch("dashboard.src.ai.get_storage_client")
    def test_upload_wires_pipeline_to_request_db(
        self,
        mock_get_storage_client,
        mock_process_voice_query,
        mock_get_ai_client,
        mock_get_home_agent,
        mock_get_receipt_printer,
        app,
    ):
        import io

        from dashboard.src.ai import ai

        mock_storage = MagicMock()
        mock_storage.upload_file.return_value = (
            "http://minio:9000/bucket/audio/test.m4a"
        )
        mock_get_storage_client.return_value = mock_storage
        mock_process_voice_query.return_value = {
            "transcription": "hi",
            "llm_response": "hello",
        }

        mock_db = MagicMock()
        app.register_blueprint(ai)

        @app.before_request
        def inject_db():
            from flask import request

            request.db = mock_db

        with app.test_client() as client:
            data = {"file": (io.BytesIO(b"fake audio"), "voice.m4a")}
            client.post(
                "/ai/audio/upload", data=data, content_type="multipart/form-data"
            )

        mock_get_home_agent.assert_called_once_with(mock_db)
        kwargs = mock_process_voice_query.call_args.kwargs
        assert kwargs["agent"] is mock_get_home_agent.return_value
        assert kwargs["voice_queries"].db is mock_db
        assert kwargs["printer"] is mock_get_receipt_printer.return_value

    def test_upload_get_not_allowed(self, app):
        from dashboard.src.ai import ai

        app.register_blueprint(ai)

        with app.test_client() as client:
            response = client.get("/ai/audio/upload")

        assert response.status_code == 405


@pytest.fixture
def db_app(app):
    """App with the AI blueprint and a mock DB session injected per request."""
    from dashboard.src.ai import ai

    app.db = MagicMock()
    app.register_blueprint(ai)

    @app.before_request
    def inject_db():
        from flask import request

        request.db = app.db

    return app


class TestAgentEndpoint:
    @patch("dashboard.src.ai.get_home_agent")
    def test_returns_agent_response(self, mock_get_home_agent, db_app):
        mock_get_home_agent.return_value.respond.return_value = "Added."

        with db_app.test_client() as client:
            response = client.post("/ai/agent", json={"message": "add milk"})

        assert response.status_code == 200
        assert response.get_json() == {"message": "add milk", "response": "Added."}
        mock_get_home_agent.assert_called_once_with(db_app.db)
        mock_get_home_agent.return_value.respond.assert_called_once_with("add milk")

    def test_missing_message(self, db_app):
        with db_app.test_client() as client:
            response = client.post("/ai/agent", json={})

        assert response.status_code == 400

    @patch("dashboard.src.ai.get_home_agent")
    def test_agent_error(self, mock_get_home_agent, db_app):
        mock_get_home_agent.return_value.respond.side_effect = Exception("boom")

        with db_app.test_client() as client:
            response = client.post("/ai/agent", json={"message": "hi"})

        assert response.status_code == 500


def minio_event(key="audio%2F20261006_clip.wav", bucket="audio"):
    return {
        "EventName": "s3:ObjectCreated:Put",
        "Records": [{"s3": {"bucket": {"name": bucket}, "object": {"key": key}}}],
    }


AUTH = {"Authorization": "Bearer secret"}


class TestAudioEventsEndpoint:
    @pytest.fixture
    def events_app(self, db_app):
        db_app.config["MINIO_EVENT_TOKEN"] = "secret"
        return db_app

    @patch("dashboard.src.ai._run_voice_query")
    @patch("dashboard.src.ai.VoiceQueryManager")
    @patch("dashboard.src.ai.get_storage_client")
    def test_processes_new_recording(
        self, mock_get_storage, mock_vq_cls, mock_run, events_app
    ):
        mock_get_storage.return_value.read_file.return_value = b"wav bytes"
        mock_vq_cls.return_value.is_processed.return_value = False
        mock_run.return_value = {"transcription": "hi", "llm_response": "hello"}

        with events_app.test_client() as client:
            response = client.post("/ai/audio/events", json=minio_event(), headers=AUTH)

        assert response.status_code == 200
        assert response.get_json()["processed"] == [
            {
                "filename": "audio/20261006_clip.wav",
                "transcription": "hi",
                "llm_response": "hello",
            }
        ]
        mock_get_storage.return_value.read_file.assert_called_once_with(
            "audio/20261006_clip.wav", "audio"
        )
        audio, filename = mock_run.call_args[0]
        assert audio.read() == b"wav bytes"
        assert filename == "audio/20261006_clip.wav"

    @patch("dashboard.src.ai._run_voice_query")
    @patch("dashboard.src.ai.VoiceQueryManager")
    @patch("dashboard.src.ai.get_storage_client")
    def test_skips_duplicate_delivery(
        self, mock_get_storage, mock_vq_cls, mock_run, events_app
    ):
        mock_vq_cls.return_value.is_processed.return_value = True

        with events_app.test_client() as client:
            response = client.post("/ai/audio/events", json=minio_event(), headers=AUTH)

        assert response.status_code == 200
        assert response.get_json()["processed"] == []
        mock_run.assert_not_called()

    @patch("dashboard.src.ai._run_voice_query")
    @patch("dashboard.src.ai.VoiceQueryManager")
    @patch("dashboard.src.ai.get_storage_client")
    def test_processing_error_returns_500(
        self, mock_get_storage, mock_vq_cls, mock_run, events_app
    ):
        mock_vq_cls.return_value.is_processed.return_value = False
        mock_run.side_effect = Exception("whisper down")

        with events_app.test_client() as client:
            response = client.post("/ai/audio/events", json=minio_event(), headers=AUTH)

        assert response.status_code == 500

    def test_rejects_wrong_token(self, events_app):
        with events_app.test_client() as client:
            response = client.post(
                "/ai/audio/events",
                json=minio_event(),
                headers={"Authorization": "Bearer nope"},
            )

        assert response.status_code == 401

    def test_rejects_when_token_not_configured(self, db_app):
        with db_app.test_client() as client:
            response = client.post("/ai/audio/events", json=minio_event(), headers=AUTH)

        assert response.status_code == 401
