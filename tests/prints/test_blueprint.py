import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.prints import prints


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["message_broker_client"] = MagicMock()
    return app


@pytest.fixture
def client(app):
    app.register_blueprint(prints)
    return app.test_client()


class TestPrintText:

    def test_success(self, client, app):
        resp = client.post(
            "/prints/",
            data=json.dumps({"text": ["Hello", "World"]}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "complete"
        app.config["message_broker_client"].send_message.assert_called_once()

    def test_empty_text(self, client, app):
        resp = client.post(
            "/prints/",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 200


class TestStreamPrint:

    @patch("dashboard.src.prints.time.sleep")
    def test_single_text_message(self, mock_sleep, client, app):
        resp = client.post(
            "/prints/stream",
            data=json.dumps({"text": "Hello"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "sent"
        app.config["message_broker_client"].send_message.assert_called_once()

    @patch("dashboard.src.prints.time.sleep")
    def test_single_cut_message(self, mock_sleep, client, app):
        resp = client.post(
            "/prints/stream",
            data=json.dumps({"cut": True}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        call_args = app.config["message_broker_client"].send_message.call_args
        body = json.loads(call_args.kwargs["body"])
        assert body["type"] == "cut"

    @patch("dashboard.src.prints.time.sleep")
    def test_batch_messages(self, mock_sleep, client, app):
        resp = client.post(
            "/prints/stream",
            data=json.dumps(
                {
                    "messages": [
                        {"text": "Line 1"},
                        {"text": "Line 2"},
                        {"cut": True},
                    ],
                    "delay": 0,
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "sent"
        assert data["count"] == 3
        assert app.config["message_broker_client"].send_message.call_count == 3

    @patch("dashboard.src.prints.time.sleep")
    def test_batch_with_delay(self, mock_sleep, client, app):
        resp = client.post(
            "/prints/stream",
            data=json.dumps(
                {
                    "messages": [
                        {"text": "Line 1"},
                        {"text": "Line 2"},
                    ],
                    "delay": 2,
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        # sleep(10) initial + sleep(2) between messages (not after last)
        assert mock_sleep.call_count == 2
