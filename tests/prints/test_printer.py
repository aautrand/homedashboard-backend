import json
from datetime import datetime
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

    @patch("dashboard.src.prints.printer.PrintManager")
    def test_print_voice_response_sends_receipt(self, mock_print_manager):
        broker = MagicMock()
        now = datetime(2026, 10, 6, 12, 18)
        mock_print_manager.print_voice_response.return_value = {"reply": 1}

        ReceiptPrinter(broker).print_voice_response("It's noon.", now)

        mock_print_manager.print_voice_response.assert_called_once_with(
            "It's noon.", now
        )
        broker.send_message.assert_called_once_with(
            exchange="", routing_key="text_print", body=json.dumps({"reply": 1})
        )

    def test_factory_uses_app_broker(self):
        app = Flask(__name__)
        broker = MagicMock()
        app.config["message_broker_client"] = broker

        with app.app_context():
            assert get_receipt_printer().broker is broker
