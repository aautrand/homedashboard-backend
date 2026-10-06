from unittest.mock import MagicMock, patch

import pytest
import requests

from dashboard.src.ai.clients.openai_transcription_client import (
    DEFAULT_MODEL,
    OpenAITranscriptionClient,
)


def _response(text):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"text": text}
    return response


class TestOpenAITranscriptionClient:
    def test_defaults(self):
        client = OpenAITranscriptionClient(api_key="sk-test")

        assert client.model == DEFAULT_MODEL == "gpt-4o-transcribe"

    @patch("dashboard.src.ai.clients.openai_transcription_client.requests.post")
    def test_transcribe_posts_multipart_request(self, mock_post):
        mock_post.return_value = _response("  hello world  ")
        audio = MagicMock()

        text = OpenAITranscriptionClient(
            api_key="sk-test", model="whisper-1"
        ).transcribe(audio, filename="clip.wav")

        assert text == "hello world"
        mock_post.assert_called_once_with(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": "Bearer sk-test"},
            files={"file": ("clip.wav", audio)},
            data={"model": "whisper-1", "response_format": "json"},
            timeout=120,
        )

    @patch("dashboard.src.ai.clients.openai_transcription_client.requests.post")
    def test_missing_text_returns_empty_string(self, mock_post):
        mock_post.return_value.json.return_value = {}

        assert OpenAITranscriptionClient(api_key="k").transcribe(MagicMock()) == ""

    @patch("dashboard.src.ai.clients.openai_transcription_client.requests.post")
    def test_http_error_includes_body(self, mock_post):
        error_response = MagicMock(status_code=401, text="invalid_api_key")
        mock_post.return_value.raise_for_status.side_effect = requests.HTTPError(
            response=error_response
        )

        with pytest.raises(Exception, match=r"\(401\): invalid_api_key"):
            OpenAITranscriptionClient(api_key="bad").transcribe(MagicMock())

    @patch("dashboard.src.ai.clients.openai_transcription_client.requests.post")
    def test_connection_error(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("no route")

        with pytest.raises(Exception, match="Failed to reach OpenAI"):
            OpenAITranscriptionClient(api_key="k").transcribe(MagicMock())
