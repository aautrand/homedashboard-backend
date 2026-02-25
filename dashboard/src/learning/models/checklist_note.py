import json
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from dashboard.src.db import Base


class ChecklistNote(Base):
    __tablename__ = "checklist_notes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    checklist_id: Mapped[int] = mapped_column(
        ForeignKey("checklists.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"ChecklistNote("
            f"id={self.id!r}, checklist_id={self.checklist_id!r}, "
            f"content={self.content!r}"
            f")"
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict())