import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.learning.routes.cards import cards_bp


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
    app.register_blueprint(cards_bp, url_prefix="/learning")

    @app.before_request
    def inject_db():
        from flask import request

        request.db = mock_db

    return app.test_client()


class TestCreateCard:

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_success(self, mock_cls, client):
        mock_card = MagicMock()
        mock_card.to_dict.return_value = {"id": 1, "title": "Q", "content": "A"}
        mock_cls.return_value.add_card.return_value = mock_card

        resp = client.post(
            "/learning/cards",
            data=json.dumps({"title": "Q", "content": "A"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert resp.get_json()["title"] == "Q"

    def test_missing_fields(self, client):
        resp = client.post(
            "/learning/cards",
            data=json.dumps({"title": "Q"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_no_body(self, client):
        resp = client.post("/learning/cards", content_type="application/json")
        assert resp.status_code == 400


class TestCreateCardsBatch:

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_success(self, mock_cls, client):
        mock_card = MagicMock()
        mock_card.to_dict.return_value = {"id": 1, "title": "Q", "content": "A"}
        mock_cls.return_value.add_card.return_value = mock_card

        resp = client.post(
            "/learning/cards/batch",
            data=json.dumps([{"title": "Q", "content": "A"}]),
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert len(resp.get_json()) == 1

    def test_not_a_list(self, client):
        resp = client.post(
            "/learning/cards/batch",
            data=json.dumps({"title": "Q"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_missing_fields_in_item(self, mock_cls, client):
        resp = client.post(
            "/learning/cards/batch",
            data=json.dumps([{"title": "Q"}]),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestGetCard:

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_found(self, mock_cls, client):
        mock_card = MagicMock()
        mock_card.to_dict.return_value = {"id": 1, "title": "Q"}
        mock_cls.return_value.get_card.return_value = mock_card

        resp = client.get("/learning/cards/1")
        assert resp.status_code == 200
        assert resp.get_json()["id"] == 1

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.get_card.return_value = None
        resp = client.get("/learning/cards/999")
        assert resp.status_code == 404


class TestUpdateCard:

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_success(self, mock_cls, client):
        mock_card = MagicMock()
        mock_card.to_dict.return_value = {"id": 1, "title": "Updated"}
        mock_cls.return_value.update_card.return_value = mock_card

        resp = client.put(
            "/learning/cards/1",
            data=json.dumps({"title": "Updated"}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.update_card.return_value = None
        resp = client.put(
            "/learning/cards/999",
            data=json.dumps({"title": "X"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_no_data(self, client):
        resp = client.put("/learning/cards/1", content_type="application/json")
        assert resp.status_code == 400

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_topic_ids_not_a_list(self, mock_cls, client):
        resp = client.put(
            "/learning/cards/1",
            data=json.dumps({"topic_ids": "not-a-list"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_topic_ids_not_integers(self, mock_cls, client):
        resp = client.put(
            "/learning/cards/1",
            data=json.dumps({"topic_ids": ["a", "b"]}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestDeleteCard:

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_success(self, mock_cls, client):
        mock_cls.return_value.delete_card.return_value = MagicMock()
        resp = client.delete("/learning/cards/1")
        assert resp.status_code == 200
        assert "deleted" in resp.get_json()["message"].lower()

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_not_found(self, mock_cls, client):
        mock_cls.return_value.delete_card.return_value = None
        resp = client.delete("/learning/cards/999")
        assert resp.status_code == 404


class TestGetCards:

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_all_cards(self, mock_cls, client):
        mock_card = MagicMock()
        mock_card.to_dict.return_value = {"id": 1}
        mock_cls.return_value.get_all_cards.return_value = [mock_card]

        resp = client.get("/learning/cards")
        assert resp.status_code == 200
        assert len(resp.get_json()) == 1

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_reviewed_true(self, mock_cls, client):
        mock_cls.return_value.get_reviewed_cards.return_value = []
        resp = client.get("/learning/cards?reviewed=true")
        assert resp.status_code == 200
        mock_cls.return_value.get_reviewed_cards.assert_called_once()

    @patch("dashboard.src.learning.routes.cards.CardManager")
    def test_reviewed_false(self, mock_cls, client):
        mock_cls.return_value.get_non_reviewed_cards.return_value = []
        resp = client.get("/learning/cards?reviewed=false")
        assert resp.status_code == 200
        mock_cls.return_value.get_non_reviewed_cards.assert_called_once()
