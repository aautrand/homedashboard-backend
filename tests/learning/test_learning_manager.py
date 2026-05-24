from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from dashboard.src.learning.learning_manager import (CardManager,
                                                     ChecklistManager,
                                                     ProblemManager,
                                                     QuizManager,
                                                     ReminderManager,
                                                     RoutineTaskManager,
                                                     SubjectManager,
                                                     TopicManager)
from dashboard.src.learning.models.card import Card, KnowledgeLevel
from dashboard.src.learning.models.checklist import Checklist
from dashboard.src.learning.models.quiz import (AnswerScore, Quiz, QuizAnswer,
                                                QuizQuestion)
from dashboard.src.learning.models.reminder import Reminder
from dashboard.src.learning.models.routine_task import RoutineTask
from dashboard.src.learning.models.subject import Subject
from dashboard.src.learning.models.topic import Topic


# ────────────────────────────────────────────
# CardManager
# ────────────────────────────────────────────
class TestCardManager:

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def mgr(self, db):
        return CardManager(db)

    def test_add_card(self, mgr, db):
        mgr.add_card(title="What is X?", content="X is Y")
        db.add.assert_called_once()
        db.commit.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.title == "What is X?"
        assert added.content == "X is Y"

    def test_get_card(self, mgr, db):
        mock_card = MagicMock(spec=Card)
        db.get.return_value = mock_card
        assert mgr.get_card(1) is mock_card
        db.get.assert_called_once_with(Card, 1)

    def test_get_card_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.get_card(999) is None

    def test_update_card(self, mgr, db):
        mock_card = MagicMock(spec=Card)
        mock_card.title = "Old"
        db.get.return_value = mock_card
        result = mgr.update_card(1, title="New")
        assert mock_card.title == "New"
        db.commit.assert_called_once()

    def test_update_card_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.update_card(999, title="X") is None
        db.commit.assert_not_called()

    def test_delete_card(self, mgr, db):
        mock_card = MagicMock(spec=Card)
        db.get.return_value = mock_card
        result = mgr.delete_card(1)
        db.delete.assert_called_once_with(mock_card)
        db.commit.assert_called_once()

    def test_delete_card_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.delete_card(999) is None
        db.delete.assert_not_called()

    def test_get_all_cards(self, mgr, db):
        cards = [MagicMock(spec=Card), MagicMock(spec=Card)]
        db.execute.return_value.scalars.return_value.all.return_value = cards
        assert mgr.get_all_cards() == cards

    def test_get_reviewed_cards(self, mgr, db):
        cards = [MagicMock(spec=Card)]
        db.execute.return_value.scalars.return_value.all.return_value = cards
        assert mgr.get_reviewed_cards() == cards

    def test_get_non_reviewed_cards(self, mgr, db):
        cards = [MagicMock(spec=Card)]
        db.execute.return_value.scalars.return_value.all.return_value = cards
        assert mgr.get_non_reviewed_cards() == cards

    def test_get_non_grokked_cards(self, mgr, db):
        cards = [MagicMock(spec=Card)]
        db.execute.return_value.scalars.return_value.all.return_value = cards
        assert mgr.get_non_grokked_cards() == cards


# ────────────────────────────────────────────
# SubjectManager
# ────────────────────────────────────────────
class TestSubjectManager:

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def mgr(self, db):
        return SubjectManager(db)

    def test_add_subject(self, mgr, db):
        mgr.add_subject(name="Math")
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_get_subject(self, mgr, db):
        mock_sub = MagicMock(spec=Subject)
        db.execute.return_value.scalar_one_or_none.return_value = mock_sub
        assert mgr.get_subject("Math") is mock_sub

    def test_get_all_subjects(self, mgr, db):
        subs = [MagicMock(spec=Subject)]
        db.execute.return_value.scalars.return_value.all.return_value = subs
        assert mgr.get_all_subjects() == subs

    def test_get_study_subjects(self, mgr, db):
        subs = [MagicMock(spec=Subject)]
        db.execute.return_value.scalars.return_value.all.return_value = subs
        assert mgr.get_study_subjects() == subs

    def test_get_subject_topics(self, mgr, db):
        topics = [MagicMock(spec=Topic)]
        db.execute.return_value.scalars.return_value.all.return_value = topics
        assert mgr.get_subject_topics(1) == topics

    def test_add_subject_topics(self, mgr, db):
        result = mgr.add_subject_topics(1, "Algebra")
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_mark_subject_studied(self, mgr, db):
        mock_sub = MagicMock(spec=Subject)
        mock_sub.times_shown = 3
        db.get.return_value = mock_sub
        mgr.mark_subject_studied(1, date(2025, 8, 15))
        assert mock_sub.times_shown == 4
        assert mock_sub.last_shown_date == date(2025, 8, 15)
        db.commit.assert_called_once()

    def test_mark_subject_studied_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.mark_subject_studied(999, date(2025, 8, 15)) is None

    def test_update_subject(self, mgr, db):
        mock_sub = MagicMock(spec=Subject)
        mock_sub.name = "Old"
        db.get.return_value = mock_sub
        mgr.update_subject(1, name="New")
        assert mock_sub.name == "New"
        db.commit.assert_called_once()


class TestCalculateStudyInterval:
    """Tests for the spaced repetition interval calculator."""

    def test_first_five_times_return_1(self):
        for i in range(5):
            assert SubjectManager.calculate_study_interval(i) == 1

    def test_times_5_to_7_return_2(self):
        for i in range(5, 8):
            assert SubjectManager.calculate_study_interval(i) == 2

    def test_times_8_to_12_return_3(self):
        for i in range(8, 13):
            assert SubjectManager.calculate_study_interval(i) == 3

    def test_times_13_to_16_return_5(self):
        for i in range(13, 17):
            assert SubjectManager.calculate_study_interval(i) == 5

    def test_times_17_to_20_return_8(self):
        for i in range(17, 21):
            assert SubjectManager.calculate_study_interval(i) == 8

    def test_times_21_to_24_return_13(self):
        for i in range(21, 25):
            assert SubjectManager.calculate_study_interval(i) == 13

    def test_times_25_plus_return_21(self):
        assert SubjectManager.calculate_study_interval(25) == 21
        assert SubjectManager.calculate_study_interval(100) == 21


class TestGetSubjectsForStudyToday:

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def mgr(self, db):
        return SubjectManager(db)

    def _make_subject(
        self, last_shown=None, times_shown=0, always_show=False, study_active=True
    ):
        s = MagicMock(spec=Subject)
        s.last_shown_date = last_shown
        s.times_shown = times_shown
        s.always_show = always_show
        s.study_active = study_active
        return s

    def test_never_shown_subject_is_eligible(self, mgr, db):
        sub = self._make_subject(last_shown=None, times_shown=0)
        db.execute.return_value.scalars.return_value.all.return_value = [sub]
        result = mgr.get_subjects_for_study_today(date(2025, 8, 15))
        assert result == [sub]

    def test_always_show_always_included(self, mgr, db):
        sub = self._make_subject(
            last_shown=date(2025, 8, 15), times_shown=100, always_show=True
        )
        db.execute.return_value.scalars.return_value.all.return_value = [sub]
        result = mgr.get_subjects_for_study_today(date(2025, 8, 15))
        assert result == [sub]

    def test_recently_shown_excluded(self, mgr, db):
        # times_shown=0 => interval=1 day, last shown today => 0 days since < 1
        sub = self._make_subject(last_shown=date(2025, 8, 15), times_shown=0)
        db.execute.return_value.scalars.return_value.all.return_value = [sub]
        result = mgr.get_subjects_for_study_today(date(2025, 8, 15))
        assert result == []

    def test_due_subject_included(self, mgr, db):
        # times_shown=0 => interval=1 day, last shown yesterday => 1 day since >= 1
        sub = self._make_subject(last_shown=date(2025, 8, 14), times_shown=0)
        db.execute.return_value.scalars.return_value.all.return_value = [sub]
        result = mgr.get_subjects_for_study_today(date(2025, 8, 15))
        assert result == [sub]

    def test_max_subjects_limit(self, mgr, db):
        subs = [self._make_subject(last_shown=None) for _ in range(5)]
        db.execute.return_value.scalars.return_value.all.return_value = subs
        result = mgr.get_subjects_for_study_today(date(2025, 8, 15), max_subjects=2)
        assert len(result) == 2

    def test_sorted_by_oldest_shown_first(self, mgr, db):
        old = self._make_subject(last_shown=date(2025, 8, 1), times_shown=0)
        new = self._make_subject(last_shown=date(2025, 8, 10), times_shown=0)
        db.execute.return_value.scalars.return_value.all.return_value = [new, old]
        result = mgr.get_subjects_for_study_today(date(2025, 8, 15), max_subjects=2)
        assert result[0] is old


# ────────────────────────────────────────────
# TopicManager
# ────────────────────────────────────────────
class TestTopicManager:

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def mgr(self, db):
        return TopicManager(db)

    def test_add_topic(self, mgr, db):
        mgr.add_topic(name="Algebra", subject_id=1)
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_add_topic_with_parent(self, mgr, db):
        mgr.add_topic(name="Linear", subject_id=1, parent_topic_id=5)
        added = db.add.call_args[0][0]
        assert added.parent_topic_id == 5

    def test_update_topic(self, mgr, db):
        mock_topic = MagicMock(spec=Topic)
        mock_topic.name = "Old"
        db.get.return_value = mock_topic
        mgr.update_topic(1, name="New")
        assert mock_topic.name == "New"

    def test_update_topic_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.update_topic(999, name="X") is None

    def test_get_all_topics(self, mgr, db):
        topics = [MagicMock(spec=Topic)]
        db.execute.return_value.scalars.return_value.all.return_value = topics
        assert mgr.get_all_topics() == topics

    def test_add_subtopic(self, mgr, db):
        mgr.add_subtopic(parent_topic_id=1, subtopic_name="Quadratic", subject_id=1)
        added = db.add.call_args[0][0]
        assert added.parent_topic_id == 1
        assert added.name == "Quadratic"


# ────────────────────────────────────────────
# ProblemManager
# ────────────────────────────────────────────
class TestProblemManager:

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def mgr(self, db):
        return ProblemManager(db)

    def test_add_problem_with_topic_id(self, mgr, db):
        problem_data = {"topic_id": 1, "content": "Solve x"}
        mgr.add_problem(problem_data)
        db.add.assert_called_once()
        db.commit.assert_called()

    def test_add_problem_creates_topic_if_not_found(self, mgr, db):
        db.execute.return_value.scalar_one_or_none.return_value = None
        problem_data = {"topic_name": "Calculus", "subject_id": 1, "content": "Solve"}
        mgr.add_problem(problem_data)
        # Should add both topic and problem
        assert db.add.call_count == 2
        assert db.commit.call_count >= 2

    def test_add_problem_reuses_existing_topic(self, mgr, db):
        mock_topic = MagicMock()
        mock_topic.id = 5
        db.execute.return_value.scalar_one_or_none.return_value = mock_topic
        problem_data = {"topic_name": "Calculus", "subject_id": 1, "content": "Solve"}
        result = mgr.add_problem(problem_data)
        # Only add the problem, not a new topic
        assert db.add.call_count == 1

    def test_add_score(self, mgr, db):
        mock_problem = MagicMock()
        mock_problem.id = 1
        mgr.add_score(mock_problem, 85)
        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.value == 85
        assert added.problem_id == 1


# ────────────────────────────────────────────
# ChecklistManager
# ────────────────────────────────────────────
class TestChecklistManager:

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def mgr(self, db):
        return ChecklistManager(db)

    def test_add_checklist(self, mgr, db):
        mgr.add_checklist(title="Morning Routine", items=["Brush teeth", "Exercise"])
        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.title == "Morning Routine"
        assert added.items == ["Brush teeth", "Exercise"]

    def test_add_checklist_default_empty_items(self, mgr, db):
        mgr.add_checklist(title="Empty")
        added = db.add.call_args[0][0]
        assert added.items == []

    def test_get_checklist(self, mgr, db):
        mock = MagicMock(spec=Checklist)
        db.get.return_value = mock
        assert mgr.get_checklist(1) is mock

    def test_get_checklist_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.get_checklist(999) is None

    def test_get_all_checklists(self, mgr, db):
        items = [MagicMock(spec=Checklist)]
        db.execute.return_value.scalars.return_value.all.return_value = items
        assert mgr.get_all_checklists() == items

    def test_update_checklist(self, mgr, db):
        mock = MagicMock(spec=Checklist)
        mock.title = "Old"
        db.get.return_value = mock
        mgr.update_checklist(1, title="New")
        assert mock.title == "New"

    def test_update_checklist_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.update_checklist(999, title="X") is None

    def test_delete_checklist(self, mgr, db):
        mock = MagicMock(spec=Checklist)
        db.get.return_value = mock
        mgr.delete_checklist(1)
        db.delete.assert_called_once_with(mock)

    def test_delete_checklist_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.delete_checklist(999) is None
        db.delete.assert_not_called()


# ────────────────────────────────────────────
# RoutineTaskManager
# ────────────────────────────────────────────
class TestRoutineTaskManagerCrud:

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def mgr(self, db):
        return RoutineTaskManager(db)

    def test_add_routine_task(self, mgr, db):
        mgr.add_routine_task(title="Workout", schedule_pattern="* * *", priority=1)
        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.title == "Workout"
        assert added.priority == 1

    def test_get_routine_task(self, mgr, db):
        mock = MagicMock(spec=RoutineTask)
        db.get.return_value = mock
        assert mgr.get_routine_task(1) is mock

    def test_get_all_routine_tasks(self, mgr, db):
        tasks = [MagicMock(spec=RoutineTask)]
        db.execute.return_value.scalars.return_value.all.return_value = tasks
        assert mgr.get_all_routine_tasks() == tasks

    def test_get_active_routine_tasks(self, mgr, db):
        tasks = [MagicMock(spec=RoutineTask)]
        db.execute.return_value.scalars.return_value.all.return_value = tasks
        assert mgr.get_active_routine_tasks() == tasks

    def test_update_routine_task(self, mgr, db):
        mock = MagicMock(spec=RoutineTask)
        mock.title = "Old"
        db.get.return_value = mock
        mgr.update_routine_task(1, title="New")
        assert mock.title == "New"

    def test_delete_routine_task(self, mgr, db):
        mock = MagicMock(spec=RoutineTask)
        db.get.return_value = mock
        mgr.delete_routine_task(1)
        db.delete.assert_called_once_with(mock)

    def test_mark_task_shown(self, mgr, db):
        mock = MagicMock(spec=RoutineTask)
        db.get.return_value = mock
        mgr.mark_task_shown(1, date(2025, 8, 15))
        assert mock.last_shown_date == date(2025, 8, 15)

    def test_mark_task_shown_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.mark_task_shown(999, date(2025, 8, 15)) is None


class TestMatchesCronPattern:
    """Tests for the cron pattern matching logic."""

    def test_wildcard_all(self):
        assert (
            RoutineTaskManager.matches_cron_pattern("* * *", date(2025, 8, 15)) is True
        )

    def test_specific_day_of_week_match(self):
        # 2025-08-15 is Friday => day_of_week = 5
        assert (
            RoutineTaskManager.matches_cron_pattern("5 * *", date(2025, 8, 15)) is True
        )

    def test_specific_day_of_week_no_match(self):
        assert (
            RoutineTaskManager.matches_cron_pattern("0 * *", date(2025, 8, 15)) is False
        )

    def test_specific_day_of_month(self):
        assert (
            RoutineTaskManager.matches_cron_pattern("* 15 *", date(2025, 8, 15)) is True
        )

    def test_specific_day_of_month_no_match(self):
        assert (
            RoutineTaskManager.matches_cron_pattern("* 1 *", date(2025, 8, 15)) is False
        )

    def test_specific_month(self):
        assert (
            RoutineTaskManager.matches_cron_pattern("* * 8", date(2025, 8, 15)) is True
        )

    def test_specific_month_no_match(self):
        assert (
            RoutineTaskManager.matches_cron_pattern("* * 1", date(2025, 8, 15)) is False
        )

    def test_range_day_of_week(self):
        # Monday(1) through Friday(5)
        assert (
            RoutineTaskManager.matches_cron_pattern("1-5 * *", date(2025, 8, 15))
            is True
        )

    def test_range_day_of_week_no_match(self):
        # 2025-08-16 is Saturday => 6, not in 1-5
        assert (
            RoutineTaskManager.matches_cron_pattern("1-5 * *", date(2025, 8, 16))
            is False
        )

    def test_list_day_of_week(self):
        assert (
            RoutineTaskManager.matches_cron_pattern("1,3,5 * *", date(2025, 8, 15))
            is True
        )

    def test_list_day_of_week_no_match(self):
        assert (
            RoutineTaskManager.matches_cron_pattern("0,2,4 * *", date(2025, 8, 15))
            is False
        )

    def test_empty_pattern(self):
        assert RoutineTaskManager.matches_cron_pattern("", date(2025, 8, 15)) is False

    def test_none_pattern(self):
        assert RoutineTaskManager.matches_cron_pattern(None, date(2025, 8, 15)) is False

    def test_invalid_format_too_few_parts(self):
        assert (
            RoutineTaskManager.matches_cron_pattern("* *", date(2025, 8, 15)) is False
        )

    def test_invalid_format_too_many_parts(self):
        assert (
            RoutineTaskManager.matches_cron_pattern("* * * *", date(2025, 8, 15))
            is False
        )

    def test_sunday_is_zero(self):
        # 2025-08-17 is Sunday => 0
        assert (
            RoutineTaskManager.matches_cron_pattern("0 * *", date(2025, 8, 17)) is True
        )


class TestMatchesCronField:

    def test_wildcard(self):
        assert RoutineTaskManager._matches_cron_field("*", 5, 0, 6) is True

    def test_exact_match(self):
        assert RoutineTaskManager._matches_cron_field("5", 5, 0, 6) is True

    def test_exact_no_match(self):
        assert RoutineTaskManager._matches_cron_field("3", 5, 0, 6) is False

    def test_range_in(self):
        assert RoutineTaskManager._matches_cron_field("1-5", 3, 0, 6) is True

    def test_range_out(self):
        assert RoutineTaskManager._matches_cron_field("1-3", 5, 0, 6) is False

    def test_list_in(self):
        assert RoutineTaskManager._matches_cron_field("1,3,5", 3, 0, 6) is True

    def test_list_out(self):
        assert RoutineTaskManager._matches_cron_field("1,3,5", 4, 0, 6) is False

    def test_invalid_range(self):
        assert RoutineTaskManager._matches_cron_field("a-b", 5, 0, 6) is False

    def test_invalid_list(self):
        assert RoutineTaskManager._matches_cron_field("a,b", 5, 0, 6) is False

    def test_invalid_single(self):
        assert RoutineTaskManager._matches_cron_field("abc", 5, 0, 6) is False


class TestGetTasksForDate:

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def mgr(self, db):
        return RoutineTaskManager(db)

    def _make_task(
        self, interval_days=None, schedule_pattern=None, last_shown=None, active=True
    ):
        t = MagicMock(spec=RoutineTask)
        t.interval_days = interval_days
        t.schedule_pattern = schedule_pattern
        t.last_shown_date = last_shown
        t.active = active
        return t

    def test_interval_never_shown(self, mgr, db):
        task = self._make_task(interval_days=3, last_shown=None)
        db.execute.return_value.scalars.return_value.all.return_value = [task]
        result = mgr.get_tasks_for_date(date(2025, 8, 15))
        assert task in result

    def test_interval_due(self, mgr, db):
        task = self._make_task(interval_days=3, last_shown=date(2025, 8, 12))
        db.execute.return_value.scalars.return_value.all.return_value = [task]
        result = mgr.get_tasks_for_date(date(2025, 8, 15))
        assert task in result

    def test_interval_not_due(self, mgr, db):
        task = self._make_task(interval_days=3, last_shown=date(2025, 8, 14))
        db.execute.return_value.scalars.return_value.all.return_value = [task]
        result = mgr.get_tasks_for_date(date(2025, 8, 15))
        assert task not in result

    def test_cron_pattern_match(self, mgr, db):
        task = self._make_task(schedule_pattern="* * *")
        db.execute.return_value.scalars.return_value.all.return_value = [task]
        result = mgr.get_tasks_for_date(date(2025, 8, 15))
        assert task in result

    def test_cron_pattern_no_match(self, mgr, db):
        task = self._make_task(schedule_pattern="0 * *")  # Sunday only
        db.execute.return_value.scalars.return_value.all.return_value = [task]
        result = mgr.get_tasks_for_date(date(2025, 8, 15))  # Friday
        assert task not in result

    def test_no_schedule_not_shown(self, mgr, db):
        task = self._make_task()  # No interval or pattern
        db.execute.return_value.scalars.return_value.all.return_value = [task]
        result = mgr.get_tasks_for_date(date(2025, 8, 15))
        assert task not in result


# ────────────────────────────────────────────
# ReminderManager
# ────────────────────────────────────────────
class TestReminderManager:

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def mgr(self, db):
        return ReminderManager(db)

    def test_add_reminder(self, mgr, db):
        mgr.add_reminder(title="Drink water")
        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.title == "Drink water"
        assert added.active is True

    def test_add_reminder_inactive(self, mgr, db):
        mgr.add_reminder(title="Old", active=False)
        added = db.add.call_args[0][0]
        assert added.active is False

    def test_get_reminder(self, mgr, db):
        mock = MagicMock(spec=Reminder)
        db.get.return_value = mock
        assert mgr.get_reminder(1) is mock

    def test_get_reminder_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.get_reminder(999) is None

    def test_get_all_reminders(self, mgr, db):
        items = [MagicMock(spec=Reminder)]
        db.execute.return_value.scalars.return_value.all.return_value = items
        assert mgr.get_all_reminders() == items

    def test_get_active_reminders(self, mgr, db):
        items = [MagicMock(spec=Reminder)]
        db.execute.return_value.scalars.return_value.all.return_value = items
        assert mgr.get_active_reminders() == items

    def test_get_reminders_by_status(self, mgr, db):
        items = [MagicMock(spec=Reminder)]
        db.execute.return_value.scalars.return_value.all.return_value = items
        assert mgr.get_reminders_by_status(True) == items

    def test_update_reminder(self, mgr, db):
        mock = MagicMock(spec=Reminder)
        mock.title = "Old"
        db.get.return_value = mock
        mgr.update_reminder(1, title="New")
        assert mock.title == "New"

    def test_update_reminder_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.update_reminder(999, title="X") is None

    def test_delete_reminder(self, mgr, db):
        mock = MagicMock(spec=Reminder)
        db.get.return_value = mock
        mgr.delete_reminder(1)
        db.delete.assert_called_once_with(mock)

    def test_delete_reminder_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.delete_reminder(999) is None
        db.delete.assert_not_called()

    def test_mark_reminder_shown(self, mgr, db):
        mock = MagicMock(spec=Reminder)
        db.get.return_value = mock
        mgr.mark_reminder_shown(1, date(2025, 8, 15))
        assert mock.last_shown_date == date(2025, 8, 15)

    def test_mark_reminder_shown_not_found(self, mgr, db):
        db.get.return_value = None
        assert mgr.mark_reminder_shown(999, date(2025, 8, 15)) is None


# ────────────────────────────────────────────
# QuizManager
# ────────────────────────────────────────────
class TestQuizManager:

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def mgr(self, db):
        return QuizManager(db)

    def test_create_quiz(self, mgr, db):
        card1 = MagicMock(spec=Card)
        card1.id = 1
        card2 = MagicMock(spec=Card)
        card2.id = 2
        mgr.create_quiz([card1, card2])
        db.add.assert_called()  # Quiz + 2 QuizQuestions
        db.flush.assert_called_once()
        db.commit.assert_called_once()

    def test_get_quiz(self, mgr, db):
        mock = MagicMock(spec=Quiz)
        db.get.return_value = mock
        assert mgr.get_quiz(1) is mock

    def test_get_all_quizzes(self, mgr, db):
        quizzes = [MagicMock(spec=Quiz)]
        db.execute.return_value.scalars.return_value.all.return_value = quizzes
        assert mgr.get_all_quizzes() == quizzes

    def test_get_quiz_questions(self, mgr, db):
        qs = [MagicMock(spec=QuizQuestion)]
        db.execute.return_value.scalars.return_value.all.return_value = qs
        assert mgr.get_quiz_questions(1) == qs

    def test_record_answer(self, mgr, db):
        mock_question = MagicMock(spec=QuizQuestion)
        mock_question.card_id = 1
        mock_card = MagicMock(spec=Card)
        mock_card.consecutive_correct = 0
        mock_card.knowledge_level = 0
        mock_card.grokked = False
        db.get.side_effect = [mock_question, mock_card]

        mgr.record_answer(quiz_question_id=10, score=AnswerScore.CORRECT)

        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_get_answers_for_question(self, mgr, db):
        answers = [MagicMock(spec=QuizAnswer)]
        db.execute.return_value.scalars.return_value.all.return_value = answers
        assert mgr.get_answers_for_question(1) == answers

    def test_get_answers_for_card(self, mgr, db):
        answers = [MagicMock(spec=QuizAnswer)]
        db.execute.return_value.scalars.return_value.all.return_value = answers
        assert mgr.get_answers_for_card(1) == answers


class TestUpdateCardKnowledge:
    """Tests for the knowledge level update logic."""

    @pytest.fixture
    def mgr(self):
        return QuizManager(MagicMock())

    def _make_card(self, consecutive_correct=0, knowledge_level=0, grokked=False):
        card = MagicMock(spec=Card)
        card.consecutive_correct = consecutive_correct
        card.knowledge_level = knowledge_level
        card.grokked = grokked
        return card

    def test_correct_increments_consecutive(self, mgr):
        card = self._make_card(consecutive_correct=1)
        mgr._update_card_knowledge(card, AnswerScore.CORRECT)
        assert card.consecutive_correct == 2

    def test_incorrect_resets_consecutive(self, mgr):
        card = self._make_card(consecutive_correct=5)
        mgr._update_card_knowledge(card, AnswerScore.INCORRECT)
        assert card.consecutive_correct == 0

    def test_partial_resets_consecutive(self, mgr):
        card = self._make_card(consecutive_correct=3)
        mgr._update_card_knowledge(card, AnswerScore.PARTIAL)
        assert card.consecutive_correct == 0

    def test_mastery_at_threshold(self, mgr):
        card = self._make_card(consecutive_correct=2)  # Will become 3 after correct
        mgr._update_card_knowledge(card, AnswerScore.CORRECT)
        assert card.knowledge_level == KnowledgeLevel.MASTERED
        assert card.grokked is True

    def test_known_at_two_consecutive(self, mgr):
        card = self._make_card(consecutive_correct=1)  # Will become 2
        mgr._update_card_knowledge(card, AnswerScore.CORRECT)
        assert card.knowledge_level == KnowledgeLevel.KNOWN

    def test_single_correct_at_least_familiar(self, mgr):
        card = self._make_card(consecutive_correct=0, knowledge_level=0)
        mgr._update_card_knowledge(card, AnswerScore.CORRECT)
        assert card.knowledge_level == KnowledgeLevel.FAMILIAR

    def test_partial_at_least_learning(self, mgr):
        card = self._make_card(knowledge_level=0)
        mgr._update_card_knowledge(card, AnswerScore.PARTIAL)
        assert card.knowledge_level == KnowledgeLevel.LEARNING

    def test_partial_caps_at_familiar(self, mgr):
        card = self._make_card(knowledge_level=KnowledgeLevel.KNOWN)
        mgr._update_card_knowledge(card, AnswerScore.PARTIAL)
        assert card.knowledge_level == KnowledgeLevel.FAMILIAR

    def test_incorrect_drops_to_learning(self, mgr):
        card = self._make_card(knowledge_level=KnowledgeLevel.KNOWN)
        mgr._update_card_knowledge(card, AnswerScore.INCORRECT)
        assert card.knowledge_level == KnowledgeLevel.LEARNING


class TestGetCardStats:

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def mgr(self, db):
        return QuizManager(db)

    def test_no_answers(self, mgr, db):
        db.execute.return_value.scalars.return_value.all.return_value = []
        mock_card = MagicMock(spec=Card)
        mock_card.knowledge_level = 0
        mock_card.consecutive_correct = 0
        db.get.return_value = mock_card

        stats = mgr.get_card_stats(1)
        assert stats["total_answers"] == 0
        assert stats["correct"] == 0

    def test_with_answers(self, mgr, db):
        a1 = MagicMock(score=AnswerScore.CORRECT)
        a2 = MagicMock(score=AnswerScore.CORRECT)
        a3 = MagicMock(score=AnswerScore.PARTIAL)
        a4 = MagicMock(score=AnswerScore.INCORRECT)
        db.execute.return_value.scalars.return_value.all.return_value = [a1, a2, a3, a4]
        mock_card = MagicMock(spec=Card)
        mock_card.knowledge_level = KnowledgeLevel.FAMILIAR
        mock_card.consecutive_correct = 0
        db.get.return_value = mock_card

        stats = mgr.get_card_stats(1)
        assert stats["total_answers"] == 4
        assert stats["correct"] == 2
        assert stats["partial"] == 1
        assert stats["incorrect"] == 1
        assert stats["correct_percentage"] == 50.0
