import json
from unittest.mock import MagicMock

import pytest
from flask import Flask, request

from dashboard.src.data import data
from dashboard.src.data.data_manager import DataManager
from dashboard.src.data.models.device_event import DeviceEvent


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
    app.register_blueprint(data)

    @app.before_request
    def inject_db():
        request.db = mock_db

    return app.test_client()


class TestRecordEventEndpoint:

    def test_success(self, client, mock_db):
        fake_event = MagicMock(spec=DeviceEvent)
        fake_event.id = 42
        mock_db.flush = MagicMock()

        def capture_add(obj):
            obj.id = 42

        mock_db.add.side_effect = capture_add

        resp = client.post(
            "/data/event",
            data=json.dumps({"id": "trash-button"}),
            content_type="application/json",
        )

        assert resp.status_code == 201
        body = resp.get_json()
        assert body["status"] == "ok"
        mock_db.add.assert_called_once()
        added = mock_db.add.call_args[0][0]
        assert isinstance(added, DeviceEvent)
        assert added.device_id == "trash-button"

    def test_missing_id_returns_400(self, client):
        resp = client.post(
            "/data/event",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "id is required" in resp.get_json()["error"]

    def test_empty_id_returns_400(self, client):
        resp = client.post(
            "/data/event",
            data=json.dumps({"id": ""}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestDataManager:

    def test_record_event_adds_to_db(self):
        mock_db = MagicMock()
        manager = DataManager(mock_db)
        event = manager.record_event("dog-button")

        mock_db.add.assert_called_once_with(event)
        mock_db.flush.assert_called_once()
        assert event.device_id == "dog-button"

    def test_record_event_returns_device_event(self):
        mock_db = MagicMock()
        manager = DataManager(mock_db)
        event = manager.record_event("trash-button")
        assert isinstance(event, DeviceEvent)
