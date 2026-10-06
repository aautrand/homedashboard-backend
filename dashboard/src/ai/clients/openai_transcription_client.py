import requests

# gpt-4o-transcribe is OpenAI's most accurate transcription model; swap for
# gpt-4o-mini-transcribe (cheaper) or whisper-1 via OPENAI_STT_MODEL.
DEFAULT_MODEL = "gpt-4o-transcribe"

DEFAULT_TIMEOUT = 120


class OpenAITranscriptionClient:
    """Speech-to-text backed by OpenAI's audio transcription REST API.

    Talks to the endpoint directly with `requests` rather than the `openai`
    SDK, matching the other AI clients.
    """

    BASE_URL = "https://api.openai.com/v1/audio/transcriptions"

    def __init__(
        self, api_key: str, model: str = DEFAULT_MODEL, timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Args:
            api_key: OpenAI API key.
            model: Transcription model name.
            timeout: Seconds to wait for the transcript.
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def transcribe(self, audio_file, filename: str = "audio.m4a") -> str:
        """Transcribe an audio file.

        Args:
            audio_file: A file-like object (binary) containing the audio data.
            filename: Filename hint so OpenAI can infer the format from the
                extension (mp3, m4a, wav, webm, ...).
        """
        try:
            response = requests.post(
                self.BASE_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": (filename, audio_file)},
                data={"model": self.model, "response_format": "json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            # OpenAI returns the reason in the body; the status line alone
            # does not distinguish a bad key from an unsupported format.
            raise Exception(
                f"OpenAI transcription failed ({e.response.status_code}): "
                f"{e.response.text}"
            ) from e
        except requests.RequestException as e:
            raise Exception(f"Failed to reach OpenAI: {e}") from e

        return response.json().get("text", "").strip()
