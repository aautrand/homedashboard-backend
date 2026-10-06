from sqlalchemy import select
from sqlalchemy.orm import Session

from dashboard.src.ai.models.voice_query import VoiceQuery


class VoiceQueryManager:
    """Persistence for transcribed voice queries and the agent's replies."""

    def __init__(self, db: Session):
        self.db = db

    def add_voice_query(
        self, filename: str, transcription: str, response: str
    ) -> VoiceQuery:
        voice_query = VoiceQuery(
            filename=filename, transcription=transcription, response=response
        )
        self.db.add(voice_query)
        return voice_query

    def is_processed(self, filename: str) -> bool:
        """Whether a recording has already been answered.

        Storage notifications can be delivered more than once, so callers
        check this before running the pipeline again for the same file.
        """
        stmt = select(VoiceQuery.id).where(VoiceQuery.filename == filename).limit(1)
        return self.db.execute(stmt).first() is not None
