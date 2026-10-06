"""Voice query pipeline: transcribe → agent → save to DB.

Built as a LangGraph graph so each step is a node with its own dependency,
and a silent recording ends the run before the agent is called. Nothing is
printed here; the agent prints only when asked to (its print_text tool).
"""

import logging
from typing import BinaryIO, TypedDict

from langgraph.graph import END, START, StateGraph

logger = logging.getLogger(__name__)


class VoiceState(TypedDict, total=False):
    audio: BinaryIO
    filename: str
    transcription: str
    response: str


def build_voice_graph(transcriber, agent, voice_queries):
    """
    Args:
        transcriber: Speech-to-text client exposing transcribe().
        agent: Exposes respond(text) -> str (see HomeAgent).
        voice_queries: VoiceQueryManager for persisting the exchange.
    """

    def transcribe(state: VoiceState) -> dict:
        transcription = transcriber.transcribe(
            state["audio"], filename=state["filename"]
        )
        logger.info("Transcribed %r: %r", state["filename"], transcription)
        return {"transcription": transcription}

    def has_speech(state: VoiceState) -> str:
        if state["transcription"].strip():
            return "respond"
        logger.info("No speech in %r, skipping agent", state["filename"])
        return END

    def respond(state: VoiceState) -> dict:
        response = agent.respond(state["transcription"])
        logger.info("Agent response for %r: %r", state["filename"], response)
        return {"response": response}

    def persist(state: VoiceState) -> dict:
        voice_queries.add_voice_query(
            filename=state["filename"],
            transcription=state["transcription"],
            response=state["response"],
        )
        return {}

    graph = StateGraph(VoiceState)
    graph.add_node("transcribe", transcribe)
    graph.add_node("respond", respond)
    graph.add_node("persist", persist)
    graph.add_edge(START, "transcribe")
    graph.add_conditional_edges("transcribe", has_speech, ["respond", END])
    graph.add_edge("respond", "persist")
    graph.add_edge("persist", END)
    return graph.compile()


def process_voice_query(
    audio: BinaryIO, filename: str, transcriber, agent, voice_queries
) -> dict:
    """
    Run the full voice query pipeline for one recording.

    Args:
        audio: Readable audio file object.
        filename: Remote filename (stored in MinIO) used as the DB reference.
        transcriber, agent, voice_queries: See build_voice_graph().

    Returns:
        Dict with transcription and llm_response ("" when nothing was said).
    """
    result = build_voice_graph(transcriber, agent, voice_queries).invoke(
        {"audio": audio, "filename": filename}
    )
    return {
        "transcription": result["transcription"],
        "llm_response": result.get("response", ""),
    }
