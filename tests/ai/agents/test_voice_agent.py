import io
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def audio():
    return io.BytesIO(b"fake audio content")


@pytest.fixture
def transcriber():
    """Stub speech-to-text client, injected into process_voice_query."""
    client = MagicMock()
    client.transcribe.return_value = "hello world"
    return client


@pytest.fixture
def agent():
    """Stub home agent, injected into process_voice_query."""
    home_agent = MagicMock()
    home_agent.respond.return_value = "Here is my response"
    return home_agent


@pytest.fixture
def voice_queries():
    return MagicMock()


@pytest.fixture
def run(audio, transcriber, agent, voice_queries):
    from dashboard.src.ai.agents.voice_agent import process_voice_query

    def _run():
        return process_voice_query(
            audio,
            "audio/test.m4a",
            transcriber=transcriber,
            agent=agent,
            voice_queries=voice_queries,
        )

    return _run


class TestProcessVoiceQuery:

    def test_returns_transcription_and_response(self, run):
        assert run() == {
            "transcription": "hello world",
            "llm_response": "Here is my response",
        }

    def test_transcribes_audio_with_filename(self, run, audio, transcriber):
        run()

        transcriber.transcribe.assert_called_once_with(audio, filename="audio/test.m4a")

    def test_agent_receives_transcription(self, run, transcriber, agent):
        transcriber.transcribe.return_value = "what is the weather today"

        run()

        agent.respond.assert_called_once_with("what is the weather today")

    def test_saves_voice_query(self, run, voice_queries):
        run()

        voice_queries.add_voice_query.assert_called_once_with(
            filename="audio/test.m4a",
            transcription="hello world",
            response="Here is my response",
        )

    def test_silent_recording_skips_agent(self, run, transcriber, agent, voice_queries):
        transcriber.transcribe.return_value = "   "

        result = run()

        assert result == {"transcription": "   ", "llm_response": ""}
        agent.respond.assert_not_called()
        voice_queries.add_voice_query.assert_not_called()

    def test_transcription_error_propagates(self, run, transcriber):
        transcriber.transcribe.side_effect = Exception("Whisper API error")

        with pytest.raises(Exception, match="Whisper API error"):
            run()

    def test_agent_error_propagates_without_saving(self, run, agent, voice_queries):
        agent.respond.side_effect = Exception("LLM unavailable")

        with pytest.raises(Exception, match="LLM unavailable"):
            run()

        voice_queries.add_voice_query.assert_not_called()
