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


class TestProcessVoiceQuery:

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    @patch("dashboard.src.ai.agents.voice_agent.OpenAIClient")
    def test_returns_transcription_and_response(self, mock_openai_cls, mock_print_manager, app, audio_file):
        mock_client = MagicMock()
        mock_client.transcribe.return_value = "hello world"
        mock_client.generate_chatgpt_response.return_value = "Here is my response"
        mock_openai_cls.return_value = mock_client
        mock_print_manager.print_voice_response.return_value = {}

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            result = process_voice_query(audio_file, "audio/test.m4a", MagicMock())

        assert result == {"transcription": "hello world", "llm_response": "Here is my response"}

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    @patch("dashboard.src.ai.agents.voice_agent.VoiceQuery")
    @patch("dashboard.src.ai.agents.voice_agent.OpenAIClient")
    def test_saves_voice_query_to_db(self, mock_openai_cls, mock_vq_cls, mock_print_manager, app, audio_file):
        mock_client = MagicMock()
        mock_client.transcribe.return_value = "test transcription"
        mock_client.generate_chatgpt_response.return_value = "test response"
        mock_openai_cls.return_value = mock_client
        mock_print_manager.print_voice_response.return_value = {}
        mock_vq_cls.return_value = MagicMock()

        db = MagicMock()

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            process_voice_query(audio_file, "audio/test.m4a", db)

        mock_vq_cls.assert_called_once_with(
            filename="audio/test.m4a",
            transcription="test transcription",
            response="test response",
        )
        db.add.assert_called_once_with(mock_vq_cls.return_value)

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    @patch("dashboard.src.ai.agents.voice_agent.OpenAIClient")
    def test_sends_receipt_to_broker(self, mock_openai_cls, mock_print_manager, app, audio_file):
        mock_client = MagicMock()
        mock_client.transcribe.return_value = "hello"
        mock_client.generate_chatgpt_response.return_value = "world"
        mock_openai_cls.return_value = mock_client
        receipt_data = {"sections": ["header", "body"]}
        mock_print_manager.print_voice_response.return_value = receipt_data

        mock_broker = app.config["message_broker_client"]

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            process_voice_query(audio_file, "audio/test.m4a", MagicMock())

        mock_broker.send_message.assert_called_once_with(
            exchange="",
            routing_key="text_print",
            body=json.dumps(receipt_data),
        )

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    @patch("dashboard.src.ai.agents.voice_agent.OpenAIClient")
    def test_llm_called_with_transcription_as_prompt(self, mock_openai_cls, mock_print_manager, app, audio_file):
        mock_client = MagicMock()
        mock_client.transcribe.return_value = "what is the weather today"
        mock_client.generate_chatgpt_response.return_value = "It is sunny"
        mock_openai_cls.return_value = mock_client
        mock_print_manager.print_voice_response.return_value = {}

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            process_voice_query(audio_file, "audio/test.m4a", MagicMock())

        mock_client.generate_chatgpt_response.assert_called_once_with(
            model="gpt-4o-mini",
            instructions="Respond to the text that is sent",
            prompt="what is the weather today",
        )

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    @patch("dashboard.src.ai.agents.voice_agent.OpenAIClient")
    def test_transcription_uses_correct_filename(self, mock_openai_cls, mock_print_manager, app, audio_file):
        mock_client = MagicMock()
        mock_client.transcribe.return_value = "transcribed"
        mock_client.generate_chatgpt_response.return_value = "response"
        mock_openai_cls.return_value = mock_client
        mock_print_manager.print_voice_response.return_value = {}

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            process_voice_query(audio_file, "audio/specific_name.m4a", MagicMock())

        assert mock_client.transcribe.call_args.kwargs["filename"] == "audio/specific_name.m4a"

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    @patch("dashboard.src.ai.agents.voice_agent.OpenAIClient")
    def test_transcription_error_propagates(self, mock_openai_cls, mock_print_manager, app, audio_file):
        mock_client = MagicMock()
        mock_client.transcribe.side_effect = Exception("Whisper API error")
        mock_openai_cls.return_value = mock_client

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            with pytest.raises(Exception, match="Whisper API error"):
                process_voice_query(audio_file, "audio/test.m4a", MagicMock())

    @patch("dashboard.src.ai.agents.voice_agent.PrintManager")
    @patch("dashboard.src.ai.agents.voice_agent.OpenAIClient")
    def test_llm_error_propagates(self, mock_openai_cls, mock_print_manager, app, audio_file):
        mock_client = MagicMock()
        mock_client.transcribe.return_value = "transcription"
        mock_client.generate_chatgpt_response.side_effect = Exception("LLM unavailable")
        mock_openai_cls.return_value = mock_client

        from dashboard.src.ai.agents.voice_agent import process_voice_query

        with app.app_context():
            with pytest.raises(Exception, match="LLM unavailable"):
                process_voice_query(audio_file, "audio/test.m4a", MagicMock())