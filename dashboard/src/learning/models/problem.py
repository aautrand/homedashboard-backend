import json
import hashlib
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from dashboard.src.db import Base


class Problem(Base):
    __tablename__ = 'problems'
    id           = Column(Integer, primary_key=True)
    content      = Column(JSONB, nullable=False)             # raw JSON of the problem
    hash         = Column(String(64), nullable=False, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    topic_id     = Column(Integer, ForeignKey('topics.id'), nullable=False)

    topic  = relationship("Topic", back_populates="problems")
    # one‑to‑many → scores
    scores = relationship(
        "Score",
        back_populates="problem",
        cascade="all, delete-orphan"
    )

    @staticmethod
    def generate_hash(content: dict) -> str:
        """Stable SHA‑256 of the JSON dict (keys sorted)."""
        s = json.dumps(content, sort_keys=True)
        return hashlib.sha256(s.encode('utf-8')).hexdigest()

    def __init__(self, content: dict):
        self.content = content
        self.hash    = Problem.generate_hash(content)