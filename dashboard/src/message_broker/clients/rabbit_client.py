import pika
from flask import current_app
from pika import BlockingConnection, ConnectionParameters

from dashboard.src.message_broker.clients.base import MessageBrokerClient


class RabbitMQClient(MessageBrokerClient):

    def __init__(self):
        self.connection = self._connect()
        self.channel = self.connection.channel()

    def _connect(self):
        credentials = pika.PlainCredentials(
            current_app.config["RABBITMQ_USER"], current_app.config["RABBITMQ_PASSWORD"]
        )
        connection = BlockingConnection(
            ConnectionParameters(
                host=current_app.config["RABBITMQ_HOST"], credentials=credentials
            )
        )
        return connection

    def _ensure_connection(self):
        if self.connection.is_closed or self.channel.is_closed:
            self.connection = self._connect()
            self.channel = self.connection.channel()

    def publish(self, exchange, routing_key, body) -> None:
        try:
            self._ensure_connection()
            self.channel.queue_declare(queue=routing_key)
            self.channel.basic_publish(
                exchange=exchange, routing_key=routing_key, body=body
            )
        except pika.exceptions.AMQPConnectionError:
            self.connection = self._connect()
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=routing_key)
            self.channel.basic_publish(
                exchange=exchange, routing_key=routing_key, body=body
            )

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
