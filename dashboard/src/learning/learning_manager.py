from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from dashboard.src.learning.models.card import Card, KnowledgeLevel
from dashboard.src.learning.models.checklist import Checklist
from dashboard.src.learning.models.problem import Problem
from dashboard.src.learning.models.quiz import (
    AnswerScore,
    Quiz,
    QuizAnswer,
    QuizQuestion,
)
from dashboard.src.learning.models.reminder import Reminder
from dashboard.src.learning.models.routine_task import RoutineTask
from dashboard.src.learning.models.score import Score
from dashboard.src.learning.models.subject import Subject
from dashboard.src.learning.models.topic import Topic


class CardManager:
    def __init__(self, db: Session):
        self.db = db

    def add_card(self, title: str, content: str):
        card = Card(title=title, content=content)
        self.db.add(card)
        self.db.commit()
        return card

    def update_card(self, card_id: int, **kwargs):
        card = self.db.get(Card, card_id)
        if card:
            for key, value in kwargs.items():
                if hasattr(card, key):
                    setattr(card, key, value)
            self.db.commit()
        return card

    def delete_card(self, card_id: int):
        card = self.db.get(Card, card_id)
        if card:
            self.db.delete(card)
            self.db.commit()
        return card

    def get_reviewed_cards(self):
        stmt = select(Card).where(Card.reviewed == True)
        return self.db.execute(stmt).scalars().all()

    def get_non_reviewed_cards(self):
        stmt = select(Card).where(Card.reviewed == False)
        return self.db.execute(stmt).scalars().all()

    def get_card(self, card_id: int):
        return self.db.get(Card, card_id)

    def get_all_cards(self):
        stmt = select(Card)
        return self.db.execute(stmt).scalars().all()

    def get_non_grokked_cards(self):
        """Get all cards that have not been grokked and are not up for review."""
        stmt = (
            select(Card)
            .where(Card.grokked == False, Card.reviewed == True)
            .order_by(Card.created_date.desc())
        )
        return self.db.execute(stmt).scalars().all()


class SubjectManager:
    def __init__(self, db: Session):
        self.db = db

    def get_subject(self, name: str):
        stmt = select(Subject).where(Subject.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def add_subject(self, name: str):
        subject = Subject(name=name)
        self.db.add(subject)
        self.db.commit()
        return subject

    def get_subject_topics(self, subject_id: int):
        stmt = select(Topic).where(Topic.subject_id == subject_id)
        return self.db.execute(stmt).scalars().all()

    def add_subject_topics(self, subject_id: int, topic_name: str):
        topic = Topic(name=topic_name, subject_id=subject_id)
        self.db.add(topic)
        self.db.commit()
        return topic

    def get_all_subjects(self):
        stmt = select(Subject)
        return self.db.execute(stmt).scalars().all()

    def get_study_subjects(self):
        """Get all subjects with study_active=True."""
        stmt = select(Subject).where(Subject.study_active == True)
        return self.db.execute(stmt).scalars().all()

    @staticmethod
    def calculate_study_interval(times_shown: int) -> int:
        """
        Calculate the interval in days based on times_shown using a flattened logarithmic pattern.
        Pattern: 1,1,1,1,1, 2,2,2, 3,3,3,3,3, 5,5,5,5, 8,8,8,8, 13,13,13,13, ...
        """
        # Define intervals: (interval_days, repetition_count)
        intervals = [
            (1, 5),  # Show 0-4:   1 day interval, 5 times
            (2, 3),  # Show 5-7:   2 day interval, 3 times
            (3, 5),  # Show 8-12:  3 day interval, 5 times
            (5, 4),  # Show 13-16: 5 day interval, 4 times
            (8, 4),  # Show 17-20: 8 day interval, 4 times
            (13, 4),  # Show 21-24: 13 day interval, 4 times
            (21, 999),  # Show 25+:   21 day interval, indefinitely
        ]

        count = 0
        for interval_days, repetitions in intervals:
            if times_shown < count + repetitions:
                return interval_days
            count += repetitions

        # Fallback (should never reach here)
        return 21

    def get_subjects_for_study_today(self, today: date, max_subjects: int = 1):
        """
        Get subjects that should be studied today based on spaced repetition.
        Returns at most max_subjects, prioritizing round-robin (oldest last_shown_date first).
        Subjects with always_show=True are always included regardless of interval.
        """
        study_subjects = self.get_study_subjects()
        eligible = []

        for subject in study_subjects:
            # Always include subjects with always_show=True
            if subject.always_show:
                eligible.append(subject)
                continue

            # Never shown before
            if subject.last_shown_date is None:
                eligible.append(subject)
                continue

            # Calculate required interval
            required_interval = self.calculate_study_interval(subject.times_shown)

            # Check if enough days have passed
            days_since = (today - subject.last_shown_date).days
            if days_since >= required_interval:
                eligible.append(subject)

        # Sort by last_shown_date (None first, then oldest)
        # This creates round-robin behavior
        eligible.sort(key=lambda s: s.last_shown_date or date.min)

        # Return at most max_subjects
        return eligible[:max_subjects]

    def mark_subject_studied(self, subject_id: int, studied_date: date):
        """Mark a subject as studied, incrementing times_shown and updating last_shown_date."""
        subject = self.db.get(Subject, subject_id)
        if subject:
            subject.times_shown += 1
            subject.last_shown_date = studied_date
            self.db.commit()
        return subject

    def update_subject(self, subject_id: int, **kwargs):
        """Update a subject."""
        subject = self.db.get(Subject, subject_id)
        if subject:
            for key, value in kwargs.items():
                if hasattr(subject, key):
                    setattr(subject, key, value)
            self.db.commit()
        return subject


class TopicManager:
    def __init__(self, db: Session):
        self.db = db

    def add_topic(self, name: str, subject_id: int, parent_topic_id: int = None):
        topic = Topic(name=name, subject_id=subject_id, parent_topic_id=parent_topic_id)
        self.db.add(topic)
        self.db.commit()
        return topic

    def update_topic(self, topic_id: int, **kwargs):
        topic = self.db.get(Topic, topic_id)
        if topic:
            for key, value in kwargs.items():
                if hasattr(topic, key):
                    setattr(topic, key, value)
            self.db.commit()
        return topic

    def get_all_topics(self):
        stmt = select(Topic)
        return self.db.execute(stmt).scalars().all()

    def add_subtopic(self, parent_topic_id: int, subtopic_name: str, subject_id: int):
        subtopic = Topic(
            name=subtopic_name, subject_id=subject_id, parent_topic_id=parent_topic_id
        )
        self.db.add(subtopic)
        self.db.commit()
        return subtopic


class ProblemManager:
    def __init__(self, db: Session):
        self.db = db

    def add_problem(self, problem: dict):
        # Map problem json to Problem object
        # If topic is not in db insert it then link problem to it
        topic_id = problem.get("topic_id")
        if not topic_id:
            # If topic name is provided but no ID, try to find or create topic
            topic_name = problem.get("topic_name")
            subject_id = problem.get("subject_id")
            if topic_name and subject_id:
                stmt = select(Topic).where(
                    Topic.name == topic_name, Topic.subject_id == subject_id
                )
                topic = self.db.execute(stmt).scalar_one_or_none()
                if not topic:
                    topic = Topic(name=topic_name, subject_id=subject_id)
                    self.db.add(topic)
                    self.db.commit()
                topic_id = topic.id

        problem_obj = Problem(content=problem)
        problem_obj.topic_id = topic_id
        self.db.add(problem_obj)
        self.db.commit()
        return problem_obj

    def add_score(self, problem: Problem, score: int):
        score_obj = Score(value=score)
        score_obj.problem_id = problem.id
        self.db.add(score_obj)
        self.db.commit()
        return score_obj


class ChecklistManager:
    def __init__(self, db: Session):
        self.db = db

    def add_checklist(self, title: str, items: list[str] = None):
        if items is None:
            items = []
        checklist = Checklist(title=title, items=items)
        self.db.add(checklist)
        self.db.commit()
        return checklist

    def get_checklist(self, checklist_id: int):
        return self.db.get(Checklist, checklist_id)

    def get_all_checklists(self):
        stmt = select(Checklist)
        return self.db.execute(stmt).scalars().all()

    def update_checklist(self, checklist_id: int, **kwargs):
        checklist = self.db.get(Checklist, checklist_id)
        if checklist:
            for key, value in kwargs.items():
                if hasattr(checklist, key):
                    setattr(checklist, key, value)
            self.db.commit()
        return checklist

    def delete_checklist(self, checklist_id: int):
        checklist = self.db.get(Checklist, checklist_id)
        if checklist:
            self.db.delete(checklist)
            self.db.commit()
        return checklist


class RoutineTaskManager:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def matches_cron_pattern(pattern: str, check_date: date) -> bool:
        """
        Check if a date matches a cron pattern.
        Pattern format: "day_of_week day_of_month month"
        - day_of_week: 0-6 (0=Sunday), * for any, ranges (1-5), lists (1,3,5)
        - day_of_month: 1-31, * for any, ranges, lists
        - month: 1-12, * for any, ranges, lists
        """
        if not pattern:
            return False

        parts = pattern.split()
        if len(parts) != 3:
            return False

        dow_pattern, dom_pattern, month_pattern = parts

        # Get date components
        # Python weekday(): Monday=0, Sunday=6
        # We want: Sunday=0, Monday=1, ..., Saturday=6
        day_of_week = (check_date.weekday() + 1) % 7
        day_of_month = check_date.day
        month = check_date.month

        # Check month
        if not RoutineTaskManager._matches_cron_field(month_pattern, month, 1, 12):
            return False

        # Check day of month
        if not RoutineTaskManager._matches_cron_field(dom_pattern, day_of_month, 1, 31):
            return False

        # Check day of week
        if not RoutineTaskManager._matches_cron_field(dow_pattern, day_of_week, 0, 6):
            return False

        return True

    @staticmethod
    def _matches_cron_field(
        pattern: str, value: int, min_val: int, max_val: int
    ) -> bool:
        """
        Check if a value matches a cron field pattern.
        Supports: *, ranges (1-5), lists (1,3,5)
        """
        if pattern == "*":
            return True

        # Handle ranges (e.g., "1-5")
        if "-" in pattern:
            try:
                start, end = map(int, pattern.split("-"))
                return start <= value <= end
            except ValueError:
                return False

        # Handle lists (e.g., "1,3,5")
        if "," in pattern:
            try:
                values = list(map(int, pattern.split(",")))
                return value in values
            except ValueError:
                return False

        # Handle single value
        try:
            return int(pattern) == value
        except ValueError:
            return False

    def add_routine_task(
        self,
        title: str,
        schedule_pattern: str = None,
        interval_days: int = None,
        priority: int = 0,
        active: bool = True,
    ):
        """Add a new routine task."""
        routine_task = RoutineTask(
            title=title,
            schedule_pattern=schedule_pattern,
            interval_days=interval_days,
            priority=priority,
            active=active,
        )
        self.db.add(routine_task)
        self.db.commit()
        return routine_task

    def get_routine_task(self, task_id: int):
        """Get a specific routine task by ID."""
        return self.db.get(RoutineTask, task_id)

    def get_all_routine_tasks(self):
        """Get all routine tasks ordered by priority."""
        stmt = select(RoutineTask).order_by(RoutineTask.priority)
        return self.db.execute(stmt).scalars().all()

    def get_active_routine_tasks(self):
        """Get all active routine tasks ordered by priority."""
        stmt = (
            select(RoutineTask)
            .where(RoutineTask.active == True)
            .order_by(RoutineTask.priority)
        )
        return self.db.execute(stmt).scalars().all()

    def get_tasks_for_date(self, check_date: date):
        """
        Get all routine tasks that should be shown for a given date.
        Handles both cron patterns and interval-based scheduling.
        """
        active_tasks = self.get_active_routine_tasks()
        matching_tasks = []

        for task in active_tasks:
            should_show = False

            # Check interval-based scheduling
            if task.interval_days:
                if not task.last_shown_date:
                    should_show = True
                else:
                    days_since = (check_date - task.last_shown_date).days
                    if days_since >= task.interval_days:
                        should_show = True

            # Check cron pattern
            if task.schedule_pattern and self.matches_cron_pattern(
                task.schedule_pattern, check_date
            ):
                should_show = True

            if should_show:
                matching_tasks.append(task)

        return matching_tasks

    def update_routine_task(self, task_id: int, **kwargs):
        """Update a routine task."""
        task = self.db.get(RoutineTask, task_id)
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            self.db.commit()
        return task

    def delete_routine_task(self, task_id: int):
        """Delete a routine task."""
        task = self.db.get(RoutineTask, task_id)
        if task:
            self.db.delete(task)
            self.db.commit()
        return task

    def mark_task_shown(self, task_id: int, shown_date: date):
        """Mark a task as shown on a specific date (for interval tracking)."""
        task = self.db.get(RoutineTask, task_id)
        if task:
            task.last_shown_date = shown_date
            self.db.commit()
        return task


class ReminderManager:
    def __init__(self, db: Session):
        self.db = db

    def add_reminder(self, title: str, active: bool = True):
        """Add a new reminder."""
        reminder = Reminder(title=title, active=active)
        self.db.add(reminder)
        self.db.commit()
        return reminder

    def get_reminder(self, reminder_id: int):
        """Get a specific reminder by ID."""
        return self.db.get(Reminder, reminder_id)

    def get_all_reminders(self):
        """Get all reminders."""
        stmt = select(Reminder)
        return self.db.execute(stmt).scalars().all()

    def get_active_reminders(self):
        """Get all active reminders."""
        stmt = select(Reminder).where(Reminder.active == True)
        return self.db.execute(stmt).scalars().all()

    def get_reminders_by_status(self, active: bool):
        """Get reminders filtered by active status."""
        stmt = select(Reminder).where(Reminder.active == active)
        return self.db.execute(stmt).scalars().all()

    def update_reminder(self, reminder_id: int, **kwargs):
        """Update a reminder."""
        reminder = self.db.get(Reminder, reminder_id)
        if reminder:
            for key, value in kwargs.items():
                if hasattr(reminder, key):
                    setattr(reminder, key, value)
            self.db.commit()
        return reminder

    def delete_reminder(self, reminder_id: int):
        """Delete a reminder."""
        reminder = self.db.get(Reminder, reminder_id)
        if reminder:
            self.db.delete(reminder)
            self.db.commit()
        return reminder

    def mark_reminder_shown(self, reminder_id: int, shown_date: date):
        """Mark a reminder as shown on a specific date."""
        reminder = self.db.get(Reminder, reminder_id)
        if reminder:
            reminder.last_shown_date = shown_date
            self.db.commit()
        return reminder


class QuizManager:
    MASTERY_THRESHOLD = 3  # consecutive correct to become MASTERED

    def __init__(self, db: Session):
        self.db = db

    def create_quiz(self, cards: list[Card]) -> Quiz:
        """Create a new quiz with the given cards in order."""
        quiz = Quiz()
        self.db.add(quiz)
        self.db.flush()

        for position, card in enumerate(cards):
            quiz_question = QuizQuestion(
                quiz_id=quiz.id,
                card_id=card.id,
                position=position,
            )
            self.db.add(quiz_question)

        self.db.commit()
        return quiz

    def get_quiz(self, quiz_id: int) -> Quiz:
        """Get a quiz by ID."""
        return self.db.get(Quiz, quiz_id)

    def get_all_quizzes(self) -> list[Quiz]:
        """Get all quizzes ordered by creation date (newest first)."""
        stmt = select(Quiz).order_by(Quiz.created_date.desc())
        return self.db.execute(stmt).scalars().all()

    def get_quiz_questions(self, quiz_id: int) -> list[QuizQuestion]:
        """Get all questions for a quiz in order."""
        stmt = (
            select(QuizQuestion)
            .where(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.position)
        )
        return self.db.execute(stmt).scalars().all()

    def record_answer(self, quiz_question_id: int, score: int) -> QuizAnswer:
        """
        Record an answer for a quiz question and update the card's knowledge level.

        Args:
            quiz_question_id: The ID of the quiz question
            score: 0=incorrect, 1=partial, 2=correct (use AnswerScore enum)

        Returns:
            The created QuizAnswer
        """
        quiz_answer = QuizAnswer(
            quiz_question_id=quiz_question_id,
            score=score,
        )
        self.db.add(quiz_answer)

        # Get the card and update its knowledge level
        quiz_question = self.db.get(QuizQuestion, quiz_question_id)
        if quiz_question:
            card = self.db.get(Card, quiz_question.card_id)
            if card:
                self._update_card_knowledge(card, score)

        self.db.commit()
        return quiz_answer

    def _update_card_knowledge(self, card: Card, score: int) -> None:
        """Update a card's knowledge level based on the answer score."""
        # Update consecutive correct counter
        if score == AnswerScore.CORRECT:
            card.consecutive_correct = (card.consecutive_correct or 0) + 1
        else:
            card.consecutive_correct = 0

        # Calculate new knowledge level
        if card.consecutive_correct >= self.MASTERY_THRESHOLD:
            card.knowledge_level = KnowledgeLevel.MASTERED
            card.grokked = True  # Mark as grokked when mastered
        elif card.consecutive_correct >= 2:
            card.knowledge_level = KnowledgeLevel.KNOWN
        elif score == AnswerScore.CORRECT:
            # Single correct - at least FAMILIAR
            if (card.knowledge_level or 0) < KnowledgeLevel.FAMILIAR:
                card.knowledge_level = KnowledgeLevel.FAMILIAR
        elif score == AnswerScore.PARTIAL:
            # Partial correct - at least LEARNING, cap at FAMILIAR
            if (card.knowledge_level or 0) < KnowledgeLevel.LEARNING:
                card.knowledge_level = KnowledgeLevel.LEARNING
            elif (card.knowledge_level or 0) > KnowledgeLevel.FAMILIAR:
                card.knowledge_level = KnowledgeLevel.FAMILIAR
        else:
            # Incorrect - drop to LEARNING
            card.knowledge_level = KnowledgeLevel.LEARNING

    def get_answers_for_question(self, quiz_question_id: int) -> list[QuizAnswer]:
        """Get all answers for a specific question."""
        stmt = (
            select(QuizAnswer)
            .where(QuizAnswer.quiz_question_id == quiz_question_id)
            .order_by(QuizAnswer.created_date)
        )
        return self.db.execute(stmt).scalars().all()

    def get_answers_for_card(self, card_id: int) -> list[QuizAnswer]:
        """Get all answers for a specific card across all quizzes."""
        stmt = (
            select(QuizAnswer)
            .join(QuizQuestion)
            .where(QuizQuestion.card_id == card_id)
            .order_by(QuizAnswer.created_date)
        )
        return self.db.execute(stmt).scalars().all()

    def get_card_stats(self, card_id: int) -> dict:
        """Get statistics for a card's quiz performance."""
        answers = self.get_answers_for_card(card_id)
        card = self.db.get(Card, card_id)

        total = len(answers)
        if total == 0:
            return {
                "total_answers": 0,
                "correct": 0,
                "partial": 0,
                "incorrect": 0,
                "knowledge_level": KnowledgeLevel(card.knowledge_level or 0).name,
                "consecutive_correct": card.consecutive_correct or 0,
            }

        correct = sum(1 for a in answers if a.score == AnswerScore.CORRECT)
        partial = sum(1 for a in answers if a.score == AnswerScore.PARTIAL)
        incorrect = sum(1 for a in answers if a.score == AnswerScore.INCORRECT)

        return {
            "total_answers": total,
            "correct": correct,
            "partial": partial,
            "incorrect": incorrect,
            "correct_percentage": round(correct / total * 100, 1),
            "knowledge_level": KnowledgeLevel(card.knowledge_level or 0).name,
            "consecutive_correct": card.consecutive_correct or 0,
        }
