from unittest.mock import MagicMock, patch

import pytest
import requests


def _response(text):
    """Build a mock requests.Response carrying a Whisper server body."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"text": text}
    return mock_response


class TestWhisperClient:
    """Tests for the WhisperClient class."""

    def test_init_default_url(self):
        """Test WhisperClient falls back to the home server address."""
        from dashboard.src.ai.clients.whisper_client import WhisperClient

        client = WhisperClient()

        assert client.url == "http://localhost:8080/inference"
        assert client.timeout == 300

    def test_init_url_argument(self):
        """Test an injected url replaces the default host."""
        from dashboard.src.ai.clients.whisper_client import WhisperClient

        assert WhisperClient(url="http://whisper:8080/inference").url == (
            "http://whisper:8080/inference"
        )

    def test_init_explicit_url_kept(self):
        """Test an explicit url argument is stored as given."""
        from dashboard.src.ai.clients.whisper_client import WhisperClient

        client = WhisperClient(url="http://localhost:9000/inference")

        assert client.url == "http://localhost:9000/inference"

    @patch("dashboard.src.ai.clients.whisper_client.requests.post")
    def test_transcribe_success(self, mock_post):
        """Test transcribe returns the text field."""
        from dashboard.src.ai.clients.whisper_client import WhisperClient

        mock_post.return_value = _response("what is the weather today")

        result = WhisperClient().transcribe(MagicMock(), filename="audio/test.m4a")

        assert result == "what is the weather today"

    @patch("dashboard.src.ai.clients.whisper_client.requests.post")
    def test_transcribe_sends_multipart_upload(self, mock_post):
        """Test the file is sent as a multipart upload with its filename."""
        from dashboard.src.ai.clients.whisper_client import WhisperClient

        mock_post.return_value = _response("ok")
        audio = MagicMock()

        WhisperClient().transcribe(audio, filename="audio/test.m4a")

        args, kwargs = mock_post.call_args
        assert args[0] == "http://localhost:8080/inference"
        assert kwargs["files"] == {"file": ("audio/test.m4a", audio)}
        assert kwargs["timeout"] == 300

    @patch("dashboard.src.ai.clients.whisper_client.requests.post")
    def test_transcribe_strips_whitespace(self, mock_post):
        """Test leading/trailing whitespace is trimmed off the transcript."""
        from dashboard.src.ai.clients.whisper_client import WhisperClient

        mock_post.return_value = _response("  hello there  ")

        assert WhisperClient().transcribe(MagicMock()) == "hello there"

    @patch("dashboard.src.ai.clients.whisper_client.requests.post")
    def test_transcribe_missing_text_field(self, mock_post):
        """Test a body with no text field yields an empty string."""
        from dashboard.src.ai.clients.whisper_client import WhisperClient

        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {}

        assert WhisperClient().transcribe(MagicMock()) == ""

    @patch("dashboard.src.ai.clients.whisper_client.requests.post")
    def test_transcribe_raises_with_body_on_http_error(self, mock_post):
        """Test HTTP errors surface the server's explanation."""
        from dashboard.src.ai.clients.whisper_client import WhisperClient

        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "model not loaded"
        mock_post.return_value.raise_for_status.side_effect = requests.HTTPError(
            response=error_response
        )

        with pytest.raises(Exception, match="model not loaded"):
            WhisperClient().transcribe(MagicMock())

    @patch("dashboard.src.ai.clients.whisper_client.requests.post")
    def test_transcribe_raises_on_connection_error(self, mock_post):
        """Test an unreachable server names the URL that failed."""
        from dashboard.src.ai.clients.whisper_client import WhisperClient

        mock_post.side_effect = requests.ConnectionError("connection refused")

        with pytest.raises(Exception, match="Failed to reach Whisper at"):
            WhisperClient().transcribe(MagicMock())

    @patch("dashboard.src.ai.clients.whisper_client.requests.post")
    def test_transcribe_with_unicode(self, mock_post):
        """Test unicode transcripts survive the round trip."""
        from dashboard.src.ai.clients.whisper_client import WhisperClient

        mock_post.return_value = _response("¿cómo estás?")

        assert WhisperClient().transcribe(MagicMock()) == "¿cómo estás?"
