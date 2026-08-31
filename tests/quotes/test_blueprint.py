import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, request

from dashboard.src.quotes import quotes


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
    app.register_blueprint(quotes)

    @app.before_request
    def inject_db():
        request.db = mock_db

    return app.test_client()


def make_mock_quote(quote_id=1, text="Be here now", author=None, pinned=False):
    quote = MagicMock()
    quote.id = quote_id
    quote.to_dict.return_value = {
        "id": quote_id,
        "text": text,
        "author": author,
        "active": True,
        "pinned": pinned,
    }
    return quote


class TestCreateQuote:

    @patch("dashboard.src.quotes.QuoteManager")
    def test_success(self, mock_mgr, client):
        mock_mgr.return_value.add_quote.return_value = make_mock_quote(
            text="Slow is smooth", author="Anon"
        )

        resp = client.post(
            "/quotes",
            data=json.dumps({"text": "Slow is smooth", "author": "Anon"}),
            content_type="application/json",
        )

        assert resp.status_code == 201
        assert resp.get_json()["text"] == "Slow is smooth"
        mock_mgr.return_value.add_quote.assert_called_once_with(
            text="Slow is smooth", author="Anon", active=True
        )

    @patch("dashboard.src.quotes.QuoteManager")
    def test_missing_text(self, mock_mgr, client):
        resp = client.post(
            "/quotes",
            data=json.dumps({"author": "Anon"}),
            content_type="application/json",
        )

        assert resp.status_code == 400
        mock_mgr.return_value.add_quote.assert_not_called()

    @patch("dashboard.src.quotes.QuoteManager")
    def test_empty_body(self, mock_mgr, client):
        resp = client.post(
            "/quotes",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert resp.status_code == 400


class TestListQuotes:

    @patch("dashboard.src.quotes.QuoteManager")
    def test_returns_all(self, mock_mgr, client):
        mock_mgr.return_value.get_all_quotes.return_value = [
            make_mock_quote(1),
            make_mock_quote(2),
        ]

        resp = client.get("/quotes")

        assert resp.status_code == 200
        assert len(resp.get_json()) == 2

    @patch("dashboard.src.quotes.QuoteManager")
    def test_filters_by_active(self, mock_mgr, client):
        mock_mgr.return_value.get_quotes_by_status.return_value = [make_mock_quote(1)]

        resp = client.get("/quotes?active=false")

        assert resp.status_code == 200
        mock_mgr.return_value.get_quotes_by_status.assert_called_once_with(False)

    @patch("dashboard.src.quotes.QuoteManager")
    def test_rejects_bad_active_value(self, mock_mgr, client):
        resp = client.get("/quotes?active=maybe")

        assert resp.status_code == 400


class TestGetQuote:

    @patch("dashboard.src.quotes.QuoteManager")
    def test_success(self, mock_mgr, client):
        mock_mgr.return_value.get_quote.return_value = make_mock_quote(7)

        resp = client.get("/quotes/7")

        assert resp.status_code == 200
        assert resp.get_json()["id"] == 7

    @patch("dashboard.src.quotes.QuoteManager")
    def test_not_found(self, mock_mgr, client):
        mock_mgr.return_value.get_quote.return_value = None

        resp = client.get("/quotes/999")

        assert resp.status_code == 404


class TestUpdateQuote:

    @patch("dashboard.src.quotes.QuoteManager")
    def test_success(self, mock_mgr, client):
        mock_mgr.return_value.update_quote.return_value = make_mock_quote(
            text="Updated"
        )

        resp = client.put(
            "/quotes/1",
            data=json.dumps({"text": "Updated"}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        mock_mgr.return_value.update_quote.assert_called_once_with(1, text="Updated")

    @patch("dashboard.src.quotes.QuoteManager")
    def test_strips_pinned_field(self, mock_mgr, client):
        """Pinning must go through /quotes/pinned so only one quote is pinned."""
        mock_mgr.return_value.update_quote.return_value = make_mock_quote()

        resp = client.put(
            "/quotes/1",
            data=json.dumps({"text": "Updated", "pinned": True}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        mock_mgr.return_value.update_quote.assert_called_once_with(1, text="Updated")

    @patch("dashboard.src.quotes.QuoteManager")
    def test_only_disallowed_fields_rejected(self, mock_mgr, client):
        resp = client.put(
            "/quotes/1",
            data=json.dumps({"pinned": True}),
            content_type="application/json",
        )

        assert resp.status_code == 400
        mock_mgr.return_value.update_quote.assert_not_called()

    @patch("dashboard.src.quotes.QuoteManager")
    def test_no_data(self, mock_mgr, client):
        resp = client.put("/quotes/1", content_type="application/json")

        assert resp.status_code == 400

    @patch("dashboard.src.quotes.QuoteManager")
    def test_not_found(self, mock_mgr, client):
        mock_mgr.return_value.update_quote.return_value = None

        resp = client.put(
            "/quotes/999",
            data=json.dumps({"text": "Updated"}),
            content_type="application/json",
        )

        assert resp.status_code == 404


class TestDeleteQuote:

    @patch("dashboard.src.quotes.QuoteManager")
    def test_success(self, mock_mgr, client):
        mock_mgr.return_value.delete_quote.return_value = make_mock_quote()

        resp = client.delete("/quotes/1")

        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Quote deleted successfully"

    @patch("dashboard.src.quotes.QuoteManager")
    def test_not_found(self, mock_mgr, client):
        mock_mgr.return_value.delete_quote.return_value = None

        resp = client.delete("/quotes/999")

        assert resp.status_code == 404


class TestPinnedQuote:

    @patch("dashboard.src.quotes.QuoteManager")
    def test_get_pinned(self, mock_mgr, client):
        mock_mgr.return_value.get_pinned_quote.return_value = make_mock_quote(
            3, pinned=True
        )

        resp = client.get("/quotes/pinned")

        assert resp.status_code == 200
        assert resp.get_json()["id"] == 3

    @patch("dashboard.src.quotes.QuoteManager")
    def test_get_pinned_when_none(self, mock_mgr, client):
        mock_mgr.return_value.get_pinned_quote.return_value = None

        resp = client.get("/quotes/pinned")

        assert resp.status_code == 404

    @patch("dashboard.src.quotes.QuoteManager")
    def test_set_pinned(self, mock_mgr, client):
        mock_mgr.return_value.pin_quote.return_value = make_mock_quote(5, pinned=True)

        resp = client.put(
            "/quotes/pinned",
            data=json.dumps({"quote_id": 5}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        mock_mgr.return_value.pin_quote.assert_called_once_with(5)

    @patch("dashboard.src.quotes.QuoteManager")
    def test_set_pinned_missing_id(self, mock_mgr, client):
        resp = client.put(
            "/quotes/pinned",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert resp.status_code == 400

    @patch("dashboard.src.quotes.QuoteManager")
    def test_set_pinned_unknown_quote(self, mock_mgr, client):
        mock_mgr.return_value.pin_quote.return_value = None

        resp = client.put(
            "/quotes/pinned",
            data=json.dumps({"quote_id": 999}),
            content_type="application/json",
        )

        assert resp.status_code == 404

    @patch("dashboard.src.quotes.QuoteManager")
    def test_cycle_pinned(self, mock_mgr, client):
        mock_mgr.return_value.cycle_pinned_quote.return_value = make_mock_quote(
            8, text="Next up", pinned=True
        )

        resp = client.post("/quotes/pinned/cycle")

        assert resp.status_code == 200
        assert resp.get_json()["text"] == "Next up"
        mock_mgr.return_value.cycle_pinned_quote.assert_called_once()

    @patch("dashboard.src.quotes.QuoteManager")
    def test_cycle_pinned_with_empty_pool(self, mock_mgr, client):
        mock_mgr.return_value.cycle_pinned_quote.return_value = None

        resp = client.post("/quotes/pinned/cycle")

        assert resp.status_code == 404

    @patch("dashboard.src.quotes.QuoteManager")
    def test_clear_pinned(self, mock_mgr, client):
        mock_mgr.return_value.unpin_quote.return_value = make_mock_quote(3)

        resp = client.delete("/quotes/pinned")

        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Quote unpinned successfully"

    @patch("dashboard.src.quotes.QuoteManager")
    def test_clear_pinned_when_none(self, mock_mgr, client):
        mock_mgr.return_value.unpin_quote.return_value = None

        resp = client.delete("/quotes/pinned")

        assert resp.status_code == 404


class TestResetRotation:

    @patch("dashboard.src.quotes.QuoteManager")
    def test_success(self, mock_mgr, client):
        mock_mgr.return_value.reset_rotation.return_value = 12

        resp = client.post("/quotes/reset-rotation")

        assert resp.status_code == 200
        assert resp.get_json()["count"] == 12
