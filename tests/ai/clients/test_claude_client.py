from unittest.mock import MagicMock, patch

import pytest
import requests


def _response(content, status=200):
    """Build a mock requests.Response carrying a Messages API body."""
    mock_response = MagicMock()
    mock_response.status_code = status
    mock_response.json.return_value = {"content": content}
    return mock_response


class TestClaudeClient:
    """Tests for the ClaudeClient class."""

    def test_init_defaults(self):
        """Test ClaudeClient stores the injected key and sensible defaults."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        client = ClaudeClient(api_key="test-api-key")

        assert client.api_key == "test-api-key"
        assert client.workspace_id is None
        assert client.model == "claude-opus-5"
        assert client.timeout == 180

    def test_init_custom_model(self):
        """Test ClaudeClient accepts a model override."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        client = ClaudeClient(api_key="k", model="claude-sonnet-5")

        assert client.model == "claude-sonnet-5"

    @patch("dashboard.src.ai.clients.claude_client.requests.post")
    def test_generate_response_success(self, mock_post):
        """Test generate_response returns the text block."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        mock_post.return_value = _response([{"type": "text", "text": "Paris"}])

        result = ClaudeClient(api_key="test-api-key").generate_response(
            "What is the capital of France?"
        )

        assert result == "Paris"

    @patch("dashboard.src.ai.clients.claude_client.requests.post")
    def test_generate_response_sends_expected_request(self, mock_post):
        """Test the URL, auth headers, and payload sent to the API."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        mock_post.return_value = _response([{"type": "text", "text": "ok"}])

        ClaudeClient(api_key="test-api-key").generate_response(
            "Hello", instructions="Be terse"
        )

        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.anthropic.com/v1/messages"
        assert kwargs["headers"] == {
            "x-api-key": "test-api-key",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        assert kwargs["timeout"] == 180
        assert kwargs["json"] == {
            "model": "claude-opus-5",
            "max_tokens": 16000,
            "thinking": {"type": "adaptive"},
            "messages": [{"role": "user", "content": "Hello"}],
            "system": "Be terse",
        }

    @patch("dashboard.src.ai.clients.claude_client.requests.post")
    def test_generate_response_omits_system_when_no_instructions(self, mock_post):
        """Test system is left out entirely rather than sent as null."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        mock_post.return_value = _response([{"type": "text", "text": "ok"}])

        ClaudeClient(api_key="test-api-key").generate_response("Hello")

        assert "system" not in mock_post.call_args.kwargs["json"]

    @patch("dashboard.src.ai.clients.claude_client.requests.post")
    def test_generate_response_model_and_max_tokens_override(self, mock_post):
        """Test per-call model and max_tokens overrides reach the payload."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        mock_post.return_value = _response([{"type": "text", "text": "ok"}])

        ClaudeClient(api_key="test-api-key").generate_response(
            "Hi", model="claude-haiku-4-5", max_tokens=256
        )

        payload = mock_post.call_args.kwargs["json"]
        assert payload["model"] == "claude-haiku-4-5"
        assert payload["max_tokens"] == 256

    @patch("dashboard.src.ai.clients.claude_client.requests.post")
    def test_generate_response_skips_thinking_blocks(self, mock_post):
        """Test thinking blocks are dropped and text blocks joined."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        mock_post.return_value = _response(
            [
                {"type": "thinking", "thinking": "internal reasoning"},
                {"type": "text", "text": "Hello "},
                {"type": "text", "text": "world"},
            ]
        )

        assert (
            ClaudeClient(api_key="test-api-key").generate_response("Hi")
            == "Hello world"
        )

    @patch("dashboard.src.ai.clients.claude_client.requests.post")
    def test_generate_response_empty_content(self, mock_post):
        """Test a response with no text blocks yields an empty string."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        mock_post.return_value = _response([])

        assert ClaudeClient(api_key="test-api-key").generate_response("Hi") == ""

    @patch("dashboard.src.ai.clients.claude_client.requests.post")
    def test_generate_response_raises_with_body_on_http_error(self, mock_post):
        """Test HTTP errors surface the API's explanation, not just the status."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        error_response = MagicMock()
        error_response.status_code = 401
        error_response.text = '{"error": {"message": "invalid x-api-key"}}'
        mock_post.return_value.raise_for_status.side_effect = requests.HTTPError(
            response=error_response
        )

        with pytest.raises(Exception, match="invalid x-api-key"):
            ClaudeClient(api_key="test-api-key").generate_response("Hi")

    @patch("dashboard.src.ai.clients.claude_client.requests.post")
    def test_generate_response_raises_on_connection_error(self, mock_post):
        """Test network failures are wrapped with context."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        mock_post.side_effect = requests.ConnectionError("no route to host")

        with pytest.raises(Exception, match="Failed to reach Claude"):
            ClaudeClient(api_key="test-api-key").generate_response("Hi")

    @patch("dashboard.src.ai.clients.claude_client.requests.post")
    def test_generate_response_with_unicode(self, mock_post):
        """Test unicode survives the round trip."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        mock_post.return_value = _response([{"type": "text", "text": "café ☕ 数学"}])

        assert (
            ClaudeClient(api_key="test-api-key").generate_response("Hi")
            == "café ☕ 数学"
        )

    @patch("dashboard.src.ai.clients.claude_client.requests.post")
    def test_workspace_id_sent_as_header(self, mock_post):
        """Test an identity-linked key's workspace is sent on the request."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        mock_post.return_value = _response([{"type": "text", "text": "ok"}])

        ClaudeClient(api_key="k", workspace_id="wrkspc_01abc").generate_response("Hi")

        headers = mock_post.call_args.kwargs["headers"]
        assert headers["anthropic-workspace-id"] == "wrkspc_01abc"

    @patch("dashboard.src.ai.clients.claude_client.requests.post")
    def test_workspace_header_omitted_when_unset(self, mock_post):
        """Test workspace-scoped keys don't get an empty workspace header."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        mock_post.return_value = _response([{"type": "text", "text": "ok"}])

        ClaudeClient(api_key="test-api-key").generate_response("Hi")

        assert "anthropic-workspace-id" not in mock_post.call_args.kwargs["headers"]

    def test_workspace_id_explicit_argument(self):
        """Test an explicit workspace_id beats the environment."""
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        assert ClaudeClient(api_key="k", workspace_id="w").workspace_id == "w"
