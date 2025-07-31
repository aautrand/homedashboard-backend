from dashboard.src.learning.models.problem import Problem


class CardManager:
    def add_card(self):
        ...

    def update_card(self):
        ...

    def delete_card(self):
        ...

    def get_non_reviewed_cards(self):
        ...


class SubjectManager:

    def get_subject(self, name):
        ...

    def add_subject(self, subject):
        ...

    def get_subject_topics(self, subject):
        ...

    def add_subject_topics(self, subject):
        ...

    def get_all_subjects(self):
        ...


class TopicManager:

    def add_topic(self, topic):
        ...

    def update_topic(self, topic):
        ...

    def get_all_topics(self):
        ...

    def add_subtopic(self, topic, subtopic):
        ...

    def add_problem(self, topic, problem):
        ...


class ProblemManager:

    def add_problem(self, problem: dict):
        # Map problem json to Problem object
        # If topic is not in db insert it then link problem to it
        ...

    def add_score(self, problem: Problem, score: int):
        ...
