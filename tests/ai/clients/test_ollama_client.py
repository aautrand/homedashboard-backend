import pytest
from unittest.mock import MagicMock, patch


class TestOllamaClient:
    """Tests for the OllamaClient class."""

    @patch("dashboard.src.ai.clients.ollama_client.ollama")
    def test_init_default_model(self, mock_ollama):
        """Test OllamaClient initializes with default model."""
        from dashboard.src.ai.clients.ollama_client import OllamaClient

        client = OllamaClient()

        assert client.model == "llama3.2:latest"
        mock_ollama.Client.assert_called_once_with(
            host="http://localhost:11434", timeout=190
        )

    @patch("dashboard.src.ai.clients.ollama_client.ollama")
    def test_init_custom_model(self, mock_ollama):
        """Test OllamaClient initializes with custom model."""
        from dashboard.src.ai.clients.ollama_client import OllamaClient

        client = OllamaClient(model="mistral:latest")

        assert client.model == "mistral:latest"

    @patch("dashboard.src.ai.clients.ollama_client.ollama")
    def test_generate_response_success(self, mock_ollama):
        """Test generate_response returns content on success."""
        from dashboard.src.ai.clients.ollama_client import OllamaClient

        mock_client_instance = MagicMock()
        mock_client_instance.chat.return_value = {
            "message": {"content": "Hello! How can I help you?"}
        }
        mock_ollama.Client.return_value = mock_client_instance

        client = OllamaClient()
        response = client.generate_response("Hello")

        assert response == "Hello! How can I help you?"
        mock_client_instance.chat.assert_called_once_with(
            "llama3.2:latest",
            messages=[{"role": "user", "content": "Hello"}],
        )

    @patch("dashboard.src.ai.clients.ollama_client.ollama")
    def test_generate_response_with_long_prompt(self, mock_ollama):
        """Test generate_response handles long prompts."""
        from dashboard.src.ai.clients.ollama_client import OllamaClient

        mock_client_instance = MagicMock()
        long_prompt = "Tell me about " + "science " * 1000
        mock_client_instance.chat.return_value = {
            "message": {"content": "Here is information about science..."}
        }
        mock_ollama.Client.return_value = mock_client_instance

        client = OllamaClient()
        response = client.generate_response(long_prompt)

        assert response == "Here is information about science..."

    @patch("dashboard.src.ai.clients.ollama_client.ollama")
    def test_generate_response_raises_exception_on_failure(self, mock_ollama):
        """Test generate_response raises exception on Ollama failure."""
        from dashboard.src.ai.clients.ollama_client import OllamaClient

        mock_client_instance = MagicMock()
        mock_client_instance.chat.side_effect = Exception("Connection refused")
        mock_ollama.Client.return_value = mock_client_instance

        client = OllamaClient()

        with pytest.raises(Exception) as exc_info:
            client.generate_response("Hello")

        assert "Failed to get response from Ollama" in str(exc_info.value)
        assert "Connection refused" in str(exc_info.value)

    @patch("dashboard.src.ai.clients.ollama_client.ollama")
    def test_chat_success(self, mock_ollama):
        """Test chat method returns content on success."""
        from dashboard.src.ai.clients.ollama_client import OllamaClient

        mock_client_instance = MagicMock()
        mock_client_instance.chat.return_value = {
            "message": {"content": "I'm doing well, thank you!"}
        }
        mock_ollama.Client.return_value = mock_client_instance

        client = OllamaClient()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]
        response = client.chat(messages)

        assert response == "I'm doing well, thank you!"
        mock_client_instance.chat.assert_called_once_with(
            "llama3.2:latest", messages=messages
        )

    @patch("dashboard.src.ai.clients.ollama_client.ollama")
    def test_chat_with_single_message(self, mock_ollama):
        """Test chat method with a single message."""
        from dashboard.src.ai.clients.ollama_client import OllamaClient

        mock_client_instance = MagicMock()
        mock_client_instance.chat.return_value = {
            "message": {"content": "Hello there!"}
        }
        mock_ollama.Client.return_value = mock_client_instance

        client = OllamaClient()
        messages = [{"role": "user", "content": "Hi"}]
        response = client.chat(messages)

        assert response == "Hello there!"

    @patch("dashboard.src.ai.clients.ollama_client.ollama")
    def test_chat_raises_exception_on_failure(self, mock_ollama):
        """Test chat raises exception on Ollama failure."""
        from dashboard.src.ai.clients.ollama_client import OllamaClient

        mock_client_instance = MagicMock()
        mock_client_instance.chat.side_effect = Exception("Timeout error")
        mock_ollama.Client.return_value = mock_client_instance

        client = OllamaClient()
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(Exception) as exc_info:
            client.chat(messages)

        assert "Failed to chat with Ollama" in str(exc_info.value)
        assert "Timeout error" in str(exc_info.value)

    @patch("dashboard.src.ai.clients.ollama_client.ollama")
    def test_chat_with_empty_messages(self, mock_ollama):
        """Test chat method with empty messages list."""
        from dashboard.src.ai.clients.ollama_client import OllamaClient

        mock_client_instance = MagicMock()
        mock_client_instance.chat.return_value = {"message": {"content": ""}}
        mock_ollama.Client.return_value = mock_client_instance

        client = OllamaClient()
        messages = []
        response = client.chat(messages)

        assert response == ""

    @patch("dashboard.src.ai.clients.ollama_client.ollama")
    def test_generate_response_with_special_characters(self, mock_ollama):
        """Test generate_response handles special characters in prompt."""
        from dashboard.src.ai.clients.ollama_client import OllamaClient

        mock_client_instance = MagicMock()
        mock_client_instance.chat.return_value = {
            "message": {"content": "Here's the code: print('Hello')"}
        }
        mock_ollama.Client.return_value = mock_client_instance

        client = OllamaClient()
        prompt = "Write code with 'quotes' and \"double quotes\" and special chars: $@#%"
        response = client.generate_response(prompt)

        assert response == "Here's the code: print('Hello')"

    @patch("dashboard.src.ai.clients.ollama_client.ollama")
    def test_uses_custom_model_in_requests(self, mock_ollama):
        """Test that custom model is used in API requests."""
        from dashboard.src.ai.clients.ollama_client import OllamaClient

        mock_client_instance = MagicMock()
        mock_client_instance.chat.return_value = {
            "message": {"content": "Response"}
        }
        mock_ollama.Client.return_value = mock_client_instance

        client = OllamaClient(model="codellama:13b")
        client.generate_response("Write code")

        mock_client_instance.chat.assert_called_once_with(
            "codellama:13b",
            messages=[{"role": "user", "content": "Write code"}],
        )