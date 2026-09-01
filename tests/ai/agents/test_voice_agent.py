import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["message_broker_client"] = MagicMock()
    return app


@pytest.fixture
def audio_file():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as f:
        f.write(b"fake audio content")
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def transcriber():
    """Stub speech-to-text client, injected into process_voice_query."""
    client = MagicMock()
    client.transcribe.return_value = "hello world"
    return client


@pytest.fixture
def llm():
    """Stub text generation client, injected into process_voice_query."""
    client = MagicMock()
    client.generate_response.return_value = "Here is my response"
    return client


class TestProcessVoiceQuery:

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    def test_returns_transcription_and_response(
        self, mock_print_manager, app, audio_file, transcriber, llm
    ):
        mock_print_manager.print_voice_response.return_value = {}

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            result = process_voice_query(
                audio_file, "audio/test.m4a", MagicMock(), transcriber, llm
            )

        assert result == {
            "transcription": "hello world",
            "llm_response": "Here is my response",
        }

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    @patch("dashboard.src.ai.agents.voice_agent.VoiceQuery")
    def test_saves_voice_query_to_db(
        self, mock_vq_cls, mock_print_manager, app, audio_file, transcriber, llm
    ):
        transcriber.transcribe.return_value = "test transcription"
        llm.generate_response.return_value = "test response"
        mock_print_manager.print_voice_response.return_value = {}
        mock_vq_cls.return_value = MagicMock()
        mock_db = MagicMock()

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            process_voice_query(audio_file, "audio/test.m4a", mock_db, transcriber, llm)

        mock_vq_cls.assert_called_once_with(
            filename="audio/test.m4a",
            transcription="test transcription",
            response="test response",
        )
        mock_db.add.assert_called_once()

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    def test_sends_receipt_to_broker(
        self, mock_print_manager, app, audio_file, transcriber, llm
    ):
        receipt_data = {"section": "value"}
        mock_print_manager.print_voice_response.return_value = receipt_data

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            process_voice_query(
                audio_file, "audio/test.m4a", MagicMock(), transcriber, llm
            )
            broker = app.config["message_broker_client"]

        broker.send_message.assert_called_once_with(
            exchange="",
            routing_key="text_print",
            body=json.dumps(receipt_data),
        )

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    def test_llm_called_with_transcription_as_prompt(
        self, mock_print_manager, app, audio_file, transcriber, llm
    ):
        transcriber.transcribe.return_value = "what is the weather today"
        mock_print_manager.print_voice_response.return_value = {}

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            process_voice_query(
                audio_file, "audio/test.m4a", MagicMock(), transcriber, llm
            )

        llm.generate_response.assert_called_once_with(
            "what is the weather today",
            instructions="Respond to the text that is sent",
        )

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    def test_transcription_uses_correct_filename(
        self, mock_print_manager, app, audio_file, transcriber, llm
    ):
        mock_print_manager.print_voice_response.return_value = {}

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            process_voice_query(
                audio_file, "audio/test.m4a", MagicMock(), transcriber, llm
            )

        assert transcriber.transcribe.call_args.kwargs["filename"] == "audio/test.m4a"

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    def test_transcription_error_propagates(
        self, mock_print_manager, app, audio_file, transcriber, llm
    ):
        transcriber.transcribe.side_effect = Exception("Whisper API error")

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            with pytest.raises(Exception, match="Whisper API error"):
                process_voice_query(
                    audio_file, "audio/test.m4a", MagicMock(), transcriber, llm
                )

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    def test_llm_error_propagates(
        self, mock_print_manager, app, audio_file, transcriber, llm
    ):
        llm.generate_response.side_effect = Exception("LLM unavailable")

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            with pytest.raises(Exception, match="LLM unavailable"):
                process_voice_query(
                    audio_file, "audio/test.m4a", MagicMock(), transcriber, llm
                )
