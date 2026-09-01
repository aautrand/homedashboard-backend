import requests

# whisper.cpp's bundled server (`whisper-server`) exposes this route; it takes a
# multipart upload named "file" and answers with {"text": ...}.
DEFAULT_URL = "http://localhost:8080/inference"

# Transcription on CPU runs roughly real-time, so a long clip needs headroom.
DEFAULT_TIMEOUT = 300


class WhisperClient:
    """Speech-to-text backed by a self-hosted Whisper HTTP server.

    Points at whisper.cpp's `/inference` route by default.
    """

    def __init__(self, url: str = DEFAULT_URL, timeout: int = DEFAULT_TIMEOUT):
        """
        Args:
            url: Full URL of the Whisper server's inference endpoint.
            timeout: Seconds to wait for the transcript.
        """
        self.url = url
        self.timeout = timeout

    def transcribe(self, audio_file, filename: str = "audio.m4a") -> str:
        """Transcribe an audio file.

        Args:
            audio_file: A file-like object (binary) containing the audio data.
            filename: Filename hint so the server can infer the format.
        """
        try:
            response = requests.post(
                self.url,
                files={"file": (filename, audio_file)},
                data={"response_format": "json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            raise Exception(
                f"Whisper request failed ({e.response.status_code}): {e.response.text}"
            ) from e
        except requests.RequestException as e:
            raise Exception(f"Failed to reach Whisper at {self.url}: {e}") from e

        return response.json().get("text", "").strip()
