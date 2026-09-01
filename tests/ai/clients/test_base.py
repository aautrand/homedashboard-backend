import pytest
from flask import Flask


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["ANTHROPIC_API_KEY"] = "test-key"
    app.config["ANTHROPIC_WORKSPACE_ID"] = "wrkspc_01test"
    app.config["WHISPER_URL"] = "http://whisper:8080/inference"
    app.config["OLLAMA_HOST"] = "http://ollama:11434"
    return app


class TestGetAIClient:
    """Tests for the get_ai_client factory."""

    def test_claude_wired_from_config(self, app):
        """Test the Claude client receives key and workspace from app config."""
        from dashboard.src.ai.clients import get_ai_client

        with app.app_context():
            client = get_ai_client("claude")

        assert client.api_key == "test-key"
        assert client.workspace_id == "wrkspc_01test"

    def test_claude_is_the_default_source(self, app):
        """Test omitting the source yields the Claude client."""
        from dashboard.src.ai.clients import get_ai_client
        from dashboard.src.ai.clients.claude_client import ClaudeClient

        with app.app_context():
            assert isinstance(get_ai_client(), ClaudeClient)

    def test_whisper_wired_from_config(self, app):
        """Test the Whisper client receives its url from app config."""
        from dashboard.src.ai.clients import get_ai_client

        with app.app_context():
            client = get_ai_client("whisper")

        assert client.url == "http://whisper:8080/inference"

    def test_ollama_wired_from_config(self, app):
        """Test the Ollama client is built against the configured host."""
        from dashboard.src.ai.clients import get_ai_client
        from dashboard.src.ai.clients.ollama_client import OllamaClient

        with app.app_context():
            assert isinstance(get_ai_client("ollama"), OllamaClient)

    def test_unknown_source_raises(self, app):
        """Test an unrecognised source is rejected."""
        from dashboard.src.ai.clients import get_ai_client

        with app.app_context():
            with pytest.raises(ValueError, match="Unknown source"):
                get_ai_client("gpt-4o")

    def test_missing_workspace_id_is_allowed(self, app):
        """Test a workspace-scoped key needs no workspace id."""
        from dashboard.src.ai.clients import get_ai_client

        app.config["ANTHROPIC_WORKSPACE_ID"] = None

        with app.app_context():
            assert get_ai_client("claude").workspace_id is None
