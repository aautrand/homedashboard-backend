import json
from unittest.mock import MagicMock, patch

from flask import Flask

from dashboard.src.prints.printer import ReceiptPrinter, get_receipt_printer


class TestReceiptPrinter:
    def test_print_receipt_sends_to_text_print_queue(self):
        broker = MagicMock()

        ReceiptPrinter(broker).print_receipt({"title": "x"})

        broker.send_message.assert_called_once_with(
            exchange="", routing_key="text_print", body=json.dumps({"title": "x"})
        )

    @patch("dashboard.src.prints.printer.PrintManager")
    def test_print_text_splits_lines(self, mock_print_manager):
        broker = MagicMock()
        mock_print_manager.print_text.return_value = {"lines": 2}

        ReceiptPrinter(broker).print_text("\nfirst\nsecond\n")

        mock_print_manager.print_text.assert_called_once_with(["first", "second"])
        broker.send_message.assert_called_once_with(
            exchange="", routing_key="text_print", body=json.dumps({"lines": 2})
        )

    def test_factory_uses_app_broker(self):
        app = Flask(__name__)
        broker = MagicMock()
        app.config["message_broker_client"] = broker

        with app.app_context():
            assert get_receipt_printer().broker is broker
