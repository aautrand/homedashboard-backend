import json
from datetime import date, datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dashboard.src.db import Base


class Subject(Base):
    __tablename__ = "subjects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_shown_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    times_shown: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    study_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    always_show: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # one‑to‑many → topics
    topics = relationship(
        "Topic", back_populates="subject", cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the current instance's attributes to a dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat() if value else None
            elif isinstance(value, date):
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
