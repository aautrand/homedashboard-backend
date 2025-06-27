import queue

from flask import current_app
from pika import BlockingConnection, ConnectionParameters

from dashboard.src.message_broker.clients.base import MessageBrokerClient


class RabbitMQClient(MessageBrokerClient):

    def __init__(self):
        self.connection = self._connect()
        self.channel = self.connection.channel()

    def _connect(self):
        connection = BlockingConnection(
            ConnectionParameters(current_app.config["RABBITMQ_HOST"])
        )
        return connection

    def publish(self, exchange, routing_key, body) -> None:
        self.channel.queue_declare(queue="hello")
        self.channel.basic_publish(
            exchange=exchange, routing_key=routing_key, body=body
        )

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
