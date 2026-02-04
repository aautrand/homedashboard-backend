import json
from datetime import date, datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Date, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from dashboard.src.db import Base


class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    last_shown_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return (
            f"Reminder("
            f"id={self.id!r}, title={self.title!r}, "
            f"active={self.active!r}"
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
                result[column.name] = value.isoformat() if value else None
            elif isinstance(value, date):
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value

        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
