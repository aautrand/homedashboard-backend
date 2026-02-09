import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.learning.routes.topics import topics_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(app, mock_db):
    app.register_blueprint(topics_bp, url_prefix="/learning")

    @app.before_request
    def inject_db():
        from flask import request
        request.db = mock_db

    return app.test_client()


class TestGetTopics:

    @patch("dashboard.src.learning.routes.topics.TopicManager")
    def test_returns_topics(self, mock_cls, client):
        mock_topic = MagicMock()
        mock_topic.id = 1
        mock_topic.name = "Algebra"
        mock_topic.subject_id = 1
        mock_topic.parent_topic_id = None
        mock_cls.return_value.get_all_topics.return_value = [mock_topic]

        resp = client.get("/learning/topics")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "Algebra"

    @patch("dashboard.src.learning.routes.topics.TopicManager")
    def test_empty(self, mock_cls, client):
        mock_cls.return_value.get_all_topics.return_value = []
        resp = client.get("/learning/topics")
        assert resp.status_code == 200
        assert resp.get_json() == []


class TestCreateTopic:

    @patch("dashboard.src.learning.routes.topics.TopicManager")
    def test_success(self, mock_cls, client):
        mock_topic = MagicMock()
        mock_topic.id = 1
        mock_topic.name = "Algebra"
        mock_cls.return_value.add_topic.return_value = mock_topic

        resp = client.post(
            "/learning/topics",
            data=json.dumps({"name": "Algebra", "subject_id": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert resp.get_json()["name"] == "Algebra"

    @patch("dashboard.src.learning.routes.topics.TopicManager")
    def test_with_parent(self, mock_cls, client):
        mock_topic = MagicMock()
        mock_topic.id = 2
        mock_topic.name = "Linear"
        mock_cls.return_value.add_topic.return_value = mock_topic

        resp = client.post(
            "/learning/topics",
            data=json.dumps({"name": "Linear", "subject_id": 1, "parent_topic_id": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        mock_cls.return_value.add_topic.assert_called_once_with(
            name="Linear", subject_id=1, parent_topic_id=1
        )

    def test_missing_name(self, client):
        resp = client.post(
            "/learning/topics",
            data=json.dumps({"subject_id": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_missing_subject_id(self, client):
        resp = client.post(
            "/learning/topics",
            data=json.dumps({"name": "Algebra"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
