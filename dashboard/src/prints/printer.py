import json

from flask import current_app

from dashboard.src.prints.print_manager import PrintManager


class ReceiptPrinter:
    """Sends built receipts to the physical printer over the message broker.

    `PrintManager` decides what a receipt looks like; this class only knows how
    to deliver one, so callers never hand-roll the broker payload.
    """

    ROUTING_KEY = "text_print"

    def __init__(self, broker):
        """
        Args:
            broker: Message broker client exposing send_message().
        """
        self.broker = broker

    def print_receipt(self, receipt: dict) -> None:
        """Queue an already-built receipt for printing."""
        self.broker.send_message(
            exchange="", routing_key=self.ROUTING_KEY, body=json.dumps(receipt)
        )

    def print_text(self, text: str) -> None:
        """Print free-form text, one receipt line per line of text."""
        self.print_receipt(PrintManager.print_text(text.strip().splitlines()))


def get_receipt_printer() -> ReceiptPrinter:
    """Build a printer wired to the app's message broker. Requires an app context."""
    return ReceiptPrinter(current_app.config["message_broker_client"])
