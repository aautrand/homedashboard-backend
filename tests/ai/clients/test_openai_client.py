from unittest.mock import MagicMock, patch

import pytest


class TestOpenAIClient:
    """Tests for the OpenAIClient class."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-api-key"})
    @patch("dashboard.src.ai.clients.openai_client.OpenAI")
    def test_init_with_api_key(self, mock_openai_class):
        """Test OpenAIClient initializes with API key from environment."""
        from dashboard.src.ai.clients.openai_client import OpenAIClient

        client = OpenAIClient()

        mock_openai_class.assert_called_once_with(api_key="test-api-key")
        assert client.client is not None

    @patch.dict("os.environ", {}, clear=True)
    @patch("dashboard.src.ai.clients.openai_client.OpenAI")
    def test_init_without_api_key(self, mock_openai_class):
        """Test OpenAIClient initializes with None API key when env var missing."""
        # Remove OPENAI_API_KEY if it exists
        import os

        from dashboard.src.ai.clients.openai_client import OpenAIClient

        os.environ.pop("OPENAI_API_KEY", None)

        client = OpenAIClient()

        mock_openai_class.assert_called_once_with(api_key=None)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-api-key"})
    @patch("dashboard.src.ai.clients.openai_client.OpenAI")
    def test_generate_chatgpt_response_success(self, mock_openai_class):
        """Test generate_chatgpt_response returns output text on success."""
        from dashboard.src.ai.clients.openai_client import OpenAIClient

        mock_response = MagicMock()
        mock_response.output_text = "This is the AI response"

        mock_client_instance = MagicMock()
        mock_client_instance.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient()
        response = client.generate_chatgpt_response(
            model="gpt-4o",
            instructions="You are a helpful assistant",
            prompt="What is 2+2?",
        )

        assert response == "This is the AI response"
        mock_client_instance.responses.create.assert_called_once_with(
            model="gpt-4o",
            instructions="You are a helpful assistant",
            input="What is 2+2?",
        )

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-api-key"})
    @patch("dashboard.src.ai.clients.openai_client.OpenAI")
    def test_generate_chatgpt_response_with_different_models(self, mock_openai_class):
        """Test generate_chatgpt_response works with different model names."""
        from dashboard.src.ai.clients.openai_client import OpenAIClient

        mock_response = MagicMock()
        mock_response.output_text = "Response"

        mock_client_instance = MagicMock()
        mock_client_instance.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient()

        # Test with different models
        models = ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "gpt-4o-mini"]
        for model in models:
            client.generate_chatgpt_response(
                model=model, instructions="Test", prompt="Test prompt"
            )

        assert mock_client_instance.responses.create.call_count == len(models)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-api-key"})
    @patch("dashboard.src.ai.clients.openai_client.OpenAI")
    def test_generate_chatgpt_response_with_long_instructions(self, mock_openai_class):
        """Test generate_chatgpt_response handles long system instructions."""
        from dashboard.src.ai.clients.openai_client import OpenAIClient

        mock_response = MagicMock()
        mock_response.output_text = "Processed response"

        mock_client_instance = MagicMock()
        mock_client_instance.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient()
        long_instructions = "You are an expert. " * 500

        response = client.generate_chatgpt_response(
            model="gpt-4o", instructions=long_instructions, prompt="Help me"
        )

        assert response == "Processed response"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-api-key"})
    @patch("dashboard.src.ai.clients.openai_client.OpenAI")
    def test_generate_chatgpt_response_with_empty_prompt(self, mock_openai_class):
        """Test generate_chatgpt_response with empty prompt."""
        from dashboard.src.ai.clients.openai_client import OpenAIClient

        mock_response = MagicMock()
        mock_response.output_text = "Empty prompt response"

        mock_client_instance = MagicMock()
        mock_client_instance.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient()
        response = client.generate_chatgpt_response(
            model="gpt-4o", instructions="Instructions", prompt=""
        )

        assert response == "Empty prompt response"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-api-key"})
    @patch("dashboard.src.ai.clients.openai_client.OpenAI")
    def test_generate_chatgpt_response_with_special_characters(self, mock_openai_class):
        """Test generate_chatgpt_response handles special characters."""
        from dashboard.src.ai.clients.openai_client import OpenAIClient

        mock_response = MagicMock()
        mock_response.output_text = '{"key": "value with $pecial ch@rs"}'

        mock_client_instance = MagicMock()
        mock_client_instance.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient()
        response = client.generate_chatgpt_response(
            model="gpt-4o",
            instructions="Process JSON with special chars: $@#%^&*()",
            prompt='Parse this: {"data": "value"}',
        )

        assert response == '{"key": "value with $pecial ch@rs"}'

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-api-key"})
    @patch("dashboard.src.ai.clients.openai_client.OpenAI")
    def test_generate_chatgpt_response_propagates_api_error(self, mock_openai_class):
        """Test generate_chatgpt_response propagates API errors."""
        from dashboard.src.ai.clients.openai_client import OpenAIClient

        mock_client_instance = MagicMock()
        mock_client_instance.responses.create.side_effect = Exception(
            "API rate limit exceeded"
        )
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient()

        with pytest.raises(Exception) as exc_info:
            client.generate_chatgpt_response(
                model="gpt-4o", instructions="Test", prompt="Test"
            )

        assert "API rate limit exceeded" in str(exc_info.value)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-api-key"})
    @patch("dashboard.src.ai.clients.openai_client.OpenAI")
    def test_generate_chatgpt_response_with_json_output(self, mock_openai_class):
        """Test generate_chatgpt_response returns valid JSON output."""
        import json

        from dashboard.src.ai.clients.openai_client import OpenAIClient

        json_response = '{"topic": "algebra", "problems": [{"id": 1, "type": "word"}]}'
        mock_response = MagicMock()
        mock_response.output_text = json_response

        mock_client_instance = MagicMock()
        mock_client_instance.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient()
        response = client.generate_chatgpt_response(
            model="gpt-4o", instructions="Return JSON", prompt="Generate problems"
        )

        # Verify response is valid JSON
        parsed = json.loads(response)
        assert parsed["topic"] == "algebra"
        assert len(parsed["problems"]) == 1

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-api-key"})
    @patch("dashboard.src.ai.clients.openai_client.OpenAI")
    def test_generate_chatgpt_response_with_unicode(self, mock_openai_class):
        """Test generate_chatgpt_response handles unicode characters."""
        from dashboard.src.ai.clients.openai_client import OpenAIClient

        mock_response = MagicMock()
        mock_response.output_text = "Response with unicode: é, ñ, 日本語, 🎉"

        mock_client_instance = MagicMock()
        mock_client_instance.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client_instance

        client = OpenAIClient()
        response = client.generate_chatgpt_response(
            model="gpt-4o",
            instructions="Handle unicode: café, niño",
            prompt="Include international characters: 你好",
        )

        assert "日本語" in response
        assert "🎉" in response
