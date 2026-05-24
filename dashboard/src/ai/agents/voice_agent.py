"""Voice query pipeline: transcribe → LLM → save to DB → print."""

import json
import logging

from flask import current_app

from dashboard.src.ai.clients.openai_client import OpenAIClient
from dashboard.src.ai.models.voice_query import VoiceQuery
from dashboard.src.prints.print_manager import PrintManager

logger = logging.getLogger(__name__)


def process_voice_query(audio_path: str, filename: str, db) -> dict:
    """
    Run the full voice query pipeline for an already-saved audio file.

    1. Transcribes audio via Whisper
    2. Gets a response from the LLM
    3. Persists filename, transcription, and response to the DB
    4. Prints the response with date/time and transcription header

    Args:
        audio_path: Local path to the audio file.
        filename: Remote filename (stored in MinIO) used as the DB reference.
        db: SQLAlchemy session (request.db).

    Returns:
        Dict with transcription and llm_response.
    """
    openai_client = OpenAIClient()

    with open(audio_path, "rb") as f:
        transcription = openai_client.transcribe(f, filename=filename)
    logger.info("Transcribed %r: %r", filename, transcription)

    llm_response = openai_client.generate_chatgpt_response(
        model="gpt-4o-mini",
        instructions="Respond to the text that is sent",
        prompt=transcription,
    )
    logger.info("LLM response for %r: %r", filename, llm_response)

    db.add(
        VoiceQuery(
            filename=filename, transcription=transcription, response=llm_response
        )
    )

    receipt_data = PrintManager.print_voice_response(transcription, llm_response)
    current_app.config["message_broker_client"].send_message(
        exchange="", routing_key="text_print", body=json.dumps(receipt_data)
    )

    return {"transcription": transcription, "llm_response": llm_response}
