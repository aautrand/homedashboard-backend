from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from dashboard.src.db import Base


class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    parent_topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)

    subject = relationship("Subject", back_populates="topics")

    # self‑referential for subtopics
    parent = relationship("Topic", remote_side=[id], back_populates="subtopics")
    subtopics = relationship(
        "Topic", back_populates="parent", cascade="all, delete-orphan"
    )
    # one‑to‑many → problems
    problems = relationship(
        "Problem", back_populates="topic", cascade="all, delete-orphan"
    )
