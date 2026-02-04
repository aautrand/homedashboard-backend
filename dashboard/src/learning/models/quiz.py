from datetime import datetime
from enum import IntEnum
from typing import List

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dashboard.src.db import Base


class AnswerScore(IntEnum):
    """Score levels for quiz answers."""

    INCORRECT = 0
    PARTIAL = 1
    CORRECT = 2


class Quiz(Base):
    """Stores a printed pop quiz with its questions in order."""

    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationship to quiz questions (ordered)
    questions: Mapped[List["QuizQuestion"]] = relationship(
        "QuizQuestion", back_populates="quiz", order_by="QuizQuestion.position"
    )

    def __repr__(self) -> str:
        return f"Quiz(id={self.id!r}, created_date={self.created_date!r})"


class QuizQuestion(Base):
    """Links a quiz to a card with position tracking."""

    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"), nullable=False)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    card: Mapped["Card"] = relationship("Card")
    answers: Mapped[List["QuizAnswer"]] = relationship(
        "QuizAnswer", back_populates="quiz_question"
    )

    def __repr__(self) -> str:
        return (
            f"QuizQuestion(id={self.id!r}, quiz_id={self.quiz_id!r}, "
            f"card_id={self.card_id!r}, position={self.position!r})"
        )


class QuizAnswer(Base):
    """Stores an answer given to a quiz question."""

    __tablename__ = "quiz_answers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quiz_question_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_questions.id"), nullable=False
    )
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Score: 0=incorrect, 1=partial, 2=correct
    score: Mapped[int] = mapped_column(SmallInteger, nullable=True)

    # Relationship
    quiz_question: Mapped["QuizQuestion"] = relationship(
        "QuizQuestion", back_populates="answers"
    )

    @property
    def score_label(self) -> str:
        """Returns human-readable score label."""
        if self.score is None:
            return "unanswered"
        return AnswerScore(self.score).name.lower()

    def __repr__(self) -> str:
        return (
            f"QuizAnswer(id={self.id!r}, quiz_question_id={self.quiz_question_id!r}, "
            f"score={self.score!r})"
        )
