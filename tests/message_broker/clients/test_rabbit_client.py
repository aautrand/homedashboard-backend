from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.message_broker.clients.base import MessageBrokerClient


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["RABBITMQ_USER"] = "user"
    app.config["RABBITMQ_PASSWORD"] = "pass"
    app.config["RABBITMQ_HOST"] = "localhost"
    return app


class TestRabbitMQClient:

    @patch("dashboard.src.message_broker.clients.rabbit_client.BlockingConnection")
    def test_init_creates_connection(self, mock_conn_cls, app):
        mock_connection = MagicMock()
        mock_conn_cls.return_value = mock_connection

        with app.app_context():
            from dashboard.src.message_broker.clients.rabbit_client import \
                RabbitMQClient

            client = RabbitMQClient()
            assert client.connection is mock_connection
            mock_connection.channel.assert_called_once()

    @patch("dashboard.src.message_broker.clients.rabbit_client.BlockingConnection")
    def test_publish(self, mock_conn_cls, app):
        mock_channel = MagicMock()
        mock_conn_cls.return_value.channel.return_value = mock_channel

        with app.app_context():
            from dashboard.src.message_broker.clients.rabbit_client import \
                RabbitMQClient

            client = RabbitMQClient()
            client.publish("exchange", "routing_key", "body")
            mock_channel.queue_declare.assert_called_once_with(queue="routing_key")
            mock_channel.basic_publish.assert_called_once_with(
                exchange="exchange", routing_key="routing_key", body="body"
            )

    @patch("dashboard.src.message_broker.clients.rabbit_client.BlockingConnection")
    def test_close(self, mock_conn_cls, app):
        with app.app_context():
            from dashboard.src.message_broker.clients.rabbit_client import \
                RabbitMQClient

            client = RabbitMQClient()
            client.close()
            mock_conn_cls.return_value.close.assert_called_once()

    @patch("dashboard.src.message_broker.clients.rabbit_client.BlockingConnection")
    def test_context_manager(self, mock_conn_cls, app):
        with app.app_context():
            from dashboard.src.message_broker.clients.rabbit_client import \
                RabbitMQClient

            with RabbitMQClient() as client:
                assert client is not None
            mock_conn_cls.return_value.close.assert_called_once()

    @patch("dashboard.src.message_broker.clients.rabbit_client.BlockingConnection")
    def test_is_message_broker_client(self, mock_conn_cls, app):
        with app.app_context():
            from dashboard.src.message_broker.clients.rabbit_client import \
                RabbitMQClient

            client = RabbitMQClient()
            assert isinstance(client, MessageBrokerClient)
