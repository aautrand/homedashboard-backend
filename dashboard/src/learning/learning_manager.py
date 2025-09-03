from sqlalchemy import select
from sqlalchemy.orm import Session

from dashboard.src.learning.models.card import Card
from dashboard.src.learning.models.problem import Problem
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
