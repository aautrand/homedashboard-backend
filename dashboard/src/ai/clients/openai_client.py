import os

from openai import OpenAI


class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

    def generate_chatgpt_response(self, model, instructions, prompt):

        response = self.client.responses.create(
            model=model,
            instructions=instructions,
            input=prompt,
        )

        return response.output_text

    def transcribe(self, audio_file, filename: str = "audio.m4a") -> str:
        """
        Transcribe an audio file using Whisper.

        Args:
            audio_file: A file-like object (binary) containing the audio data.
            filename: Filename hint so Whisper can infer the format.
        """
        transcript = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, audio_file),
        )
        return transcript.text
