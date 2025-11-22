from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from dashboard.src.learning.models.card import Card
from dashboard.src.learning.models.checklist import Checklist
from dashboard.src.learning.models.problem import Problem
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

    def get_non_reviewed_cards(self):
        stmt = select(Card).where(Card.reviewed == False)
        return self.db.execute(stmt).scalars().all()

    def get_all_cards(self):
        stmt = select(Card)
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
    def _matches_cron_field(pattern: str, value: int, min_val: int, max_val: int) -> bool:
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
