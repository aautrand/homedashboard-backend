import ollama


class OllamaClient:
    def __init__(self, model="llama3.2:latest"):
        self.client = ollama.Client(host="http://localhost:11434", timeout=190)

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
