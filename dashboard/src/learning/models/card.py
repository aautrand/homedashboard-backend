import json
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dashboard.src.db import Base


class Card(Base):
    __tablename__ = "cards"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # many‑to‑many → topics
    topics = relationship(
        "Topic", secondary="topic_card_association", back_populates="cards"
    )

    def __repr__(self) -> str:
        return (
            f"Card("
            f"id={self.id!r}, title={self.title!r}, "
            f"reviewed={self.reviewed!r}, reviewed_date={self.reviewed_date!r}"
            f")"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the current instance's attributes to a dictionary,
        converting datetime objects to strings.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                # Convert datetime to ISO format string
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value

        # Add topics as a list of topic names
        result["topics"] = [topic.name for topic in self.topics]
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
