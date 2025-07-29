from dashboard.src.db import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship


class Subject(Base):
    __tablename__ = 'subjects'
    id   = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    # one‑to‑many → topics
    topics = relationship(
        "Topic",
        back_populates="subject",
        cascade="all, delete-orphan"
    )