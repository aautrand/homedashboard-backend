from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from dashboard.src.db import Base


class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    value = Column(Integer, nullable=False)
    updated_date = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)

    problem = relationship("Problem", back_populates="scores")
