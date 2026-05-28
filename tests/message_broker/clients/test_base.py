from unittest.mock import patch

import pytest
from flask import Flask

from dashboard.src.message_broker.clients.base import (
    MessageBrokerClient,
    get_message_broker_client,
)


class TestMessageBrokerClientABC:

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            MessageBrokerClient()

    def test_send_message_delegates_to_publish(self):
        class FakeBroker(MessageBrokerClient):
            def publish(self, exchange, routing_key, body):
                self.called_with = (exchange, routing_key, body)

        broker = FakeBroker()
        broker.send_message("ex", "rk", "body")
        assert broker.called_with == ("ex", "rk", "body")


class TestGetMessageBrokerClient:

    @patch("dashboard.src.message_broker.clients.rabbit_client.BlockingConnection")
    def test_returns_rabbitmq_client(self, mock_conn_cls):
        app = Flask(__name__)
        app.config["RABBITMQ_USER"] = "user"
        app.config["RABBITMQ_PASSWORD"] = "pass"
        app.config["RABBITMQ_HOST"] = "localhost"
        with app.app_context():
            result = get_message_broker_client("RabbitMQ")
            assert result is not None

    def test_unknown_source_raises(self):
        with pytest.raises(ValueError, match="Unknown source"):
            get_message_broker_client("Unknown")
