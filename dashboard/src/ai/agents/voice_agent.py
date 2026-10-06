"""Voice query pipeline: transcribe → agent → save to DB → print reply.

Built as a LangGraph graph so each step is a node with its own dependency,
and a silent recording ends the run before the agent is called. Only the
agent's reply is printed, never the transcription. If the agent already
printed through one of its PRINTING_TOOLS, the reply is not printed again;
if the user asked not to print (skip_reply_print tool), nothing is printed.
"""

import logging
from datetime import datetime, tzinfo
from typing import BinaryIO, TypedDict

from langgraph.graph import END, START, StateGraph

from dashboard.src.ai.agents.home_tools import PRINTING_TOOLS

logger = logging.getLogger(__name__)


class VoiceState(TypedDict, total=False):
    audio: BinaryIO
    filename: str
    transcription: str
    response: str


def build_voice_graph(transcriber, agent, voice_queries, printer, tz: tzinfo = None):
    """
    Args:
        transcriber: Speech-to-text client exposing transcribe().
        agent: Exposes respond(text) -> str and used_tools (see HomeAgent).
        voice_queries: VoiceQueryManager for persisting the exchange.
        printer: ReceiptPrinter the reply is printed on.
        tz: Timezone for the receipt timestamp; None uses server time.
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

    def print_response(state: VoiceState) -> dict:
        if agent.used_tools & PRINTING_TOOLS:
            logger.info("Agent already printed for %r", state["filename"])
            return {}
        if "skip_reply_print" in agent.used_tools:
            logger.info("User asked not to print for %r", state["filename"])
            return {}
        # The exchange is already saved; failing to queue the print (broker
        # unreachable) should not fail it. Publishing succeeds whether or not a
        # printer is consuming, so an offline printer is not detected here.
        try:
            printer.print_voice_response(state["response"], datetime.now(tz))
        except Exception:
            logger.exception("Failed to print response for %r", state["filename"])
        return {}

    graph = StateGraph(VoiceState)
    graph.add_node("transcribe", transcribe)
    graph.add_node("respond", respond)
    graph.add_node("persist", persist)
    graph.add_node("print_response", print_response)
    graph.add_edge(START, "transcribe")
    graph.add_conditional_edges("transcribe", has_speech, ["respond", END])
    graph.add_edge("respond", "persist")
    graph.add_edge("persist", "print_response")
    graph.add_edge("print_response", END)
    return graph.compile()


def process_voice_query(
    audio: BinaryIO,
    filename: str,
    transcriber,
    agent,
    voice_queries,
    printer,
    tz: tzinfo = None,
) -> dict:
    """
    Run the full voice query pipeline for one recording.

    Args:
        audio: Readable audio file object.
        filename: Remote filename (stored in MinIO) used as the DB reference.
        transcriber, agent, voice_queries, printer, tz: See build_voice_graph().

    Returns:
        Dict with transcription and llm_response ("" when nothing was said).
    """
    result = build_voice_graph(transcriber, agent, voice_queries, printer, tz).invoke(
        {"audio": audio, "filename": filename}
    )
    return {
        "transcription": result["transcription"],
        "llm_response": result.get("response", ""),
    }
