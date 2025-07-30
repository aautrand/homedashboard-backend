import enum
from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from dashboard.src.db import Base

class StudyStatus(enum.Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETE    = "Complete"
    PAUSED      = "Paused"
    ARCHIVED    = "Archived"

class Study(Base):
    __tablename__ = "study"
    id           = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status       = Column(
                     Enum(StudyStatus, 
                          name="study_status_enum",   # optional: gives the DB type a name
                          native_enum=True            # use DB-native ENUM if supported
                     ),
                     default=StudyStatus.NOT_STARTED,
                     nullable=False
                   )
    topic_id     = Column(Integer, ForeignKey("topics.id"), nullable=False)

    topic = relationship("Topic", back_populates="problems")