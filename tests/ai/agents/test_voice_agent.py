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
    home_agent.used_tools = set()
    return home_agent


@pytest.fixture
def voice_queries():
    return MagicMock()


@pytest.fixture
def printer():
    return MagicMock()


@pytest.fixture
def run(audio, transcriber, agent, voice_queries, printer):
    from dashboard.src.ai.agents.voice_agent import process_voice_query

    def _run():
        return process_voice_query(
            audio,
            "audio/test.m4a",
            transcriber=transcriber,
            agent=agent,
            voice_queries=voice_queries,
            printer=printer,
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

    def test_silent_recording_skips_agent(
        self, run, transcriber, agent, voice_queries, printer
    ):
        transcriber.transcribe.return_value = "   "

        result = run()

        assert result == {"transcription": "   ", "llm_response": ""}
        agent.respond.assert_not_called()
        voice_queries.add_voice_query.assert_not_called()
        printer.print_voice_response.assert_not_called()

    def test_transcription_error_propagates(self, run, transcriber):
        transcriber.transcribe.side_effect = Exception("Whisper API error")

        with pytest.raises(Exception, match="Whisper API error"):
            run()

    def test_agent_error_propagates_without_saving(self, run, agent, voice_queries):
        agent.respond.side_effect = Exception("LLM unavailable")

        with pytest.raises(Exception, match="LLM unavailable"):
            run()

        voice_queries.add_voice_query.assert_not_called()

    def test_prints_response_not_transcription(self, run, printer):
        run()

        printer.print_voice_response.assert_called_once()
        printed = printer.print_voice_response.call_args.args
        assert printed[0] == "Here is my response"
        assert "hello world" not in str(printed)

    def test_does_not_print_twice_when_agent_printed(self, run, agent, printer):
        agent.used_tools = {"list_todos", "print_text"}

        run()

        printer.print_voice_response.assert_not_called()

    def test_does_not_print_twice_after_printing_ingredients(self, run, agent, printer):
        agent.used_tools = {"search_recipes", "print_recipe_ingredients"}

        run()

        printer.print_voice_response.assert_not_called()

    def test_does_not_print_when_user_asked_not_to(
        self, run, agent, printer, voice_queries
    ):
        agent.used_tools = {"add_todo", "skip_reply_print"}

        result = run()

        printer.print_voice_response.assert_not_called()
        assert result["llm_response"] == "Here is my response"
        voice_queries.add_voice_query.assert_called_once()

    def test_printer_failure_does_not_fail_request(self, run, printer, voice_queries):
        printer.print_voice_response.side_effect = Exception("broker down")

        assert run()["llm_response"] == "Here is my response"
        voice_queries.add_voice_query.assert_called_once()

    def test_agent_error_does_not_print(self, run, agent, printer):
        agent.respond.side_effect = Exception("LLM unavailable")

        with pytest.raises(Exception):
            run()

        printer.print_voice_response.assert_not_called()
