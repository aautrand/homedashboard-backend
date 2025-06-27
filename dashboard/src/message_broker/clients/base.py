from abc import ABC, abstractmethod


class MessageBrokerClient(ABC):

    @abstractmethod
    def publish(self, exchange: str, routing_key: str, body: str) -> None:
        """Fetch the raw JSON from whatever API."""
        ...

    def send_message(self, exchange: str, routing_key: str, body: str) -> None:
        self.publish(exchange, routing_key, body)


def get_message_broker_client(source: str = "RabbitMQ") -> MessageBrokerClient:
    if source == "RabbitMQ":
        from .rabbit_client import RabbitMQClient

        return RabbitMQClient()
    else:
        raise ValueError(f"Unknown source {source!r}")
