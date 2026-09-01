import ollama

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:latest"
DEFAULT_TIMEOUT = 190


class OllamaClient:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        model: str = DEFAULT_MODEL,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Args:
            host: Base URL of the Ollama server.
            model: Model tag to run.
            timeout: Seconds to wait for a completion.
        """
        self.client = ollama.Client(host=host, timeout=timeout)

        self.model = model

    def generate_response(self, prompt):
        messages = [
            {
                "role": "user",
                "content": prompt,
            },
        ]

        try:
            response = self.client.chat(self.model, messages=messages)
            return response["message"]["content"]

        except Exception as e:
            raise Exception(f"Failed to get response from Ollama: {e}")

    def chat(self, messages):
        try:
            response = self.client.chat(self.model, messages=messages)
            return response["message"]["content"]

        except Exception as e:
            raise Exception(f"Failed to chat with Ollama: {e}")
