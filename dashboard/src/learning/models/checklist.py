import json
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from dashboard.src.db import Base


class Checklist(Base):
    __tablename__ = "checklists"
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
    items: Mapped[List[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)

    def __repr__(self) -> str:
        return (
            f"Checklist("
            f"id={self.id!r}, title={self.title!r}, "
            f"items={self.items!r}"
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

        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
