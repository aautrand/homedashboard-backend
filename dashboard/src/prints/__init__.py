import json
import time
from flask import Blueprint, request

from dashboard import get_message_broker_client
from dashboard.src.prints.print_manager import PrintManager

prints = Blueprint('print', __name__, url_prefix='/prints')


@prints.route("/", methods=['POST'])
def print_text():
    data = request.get_json()
    text = data.get("text", [])

    print_manager = PrintManager()
    text = print_manager.print_text(text)
    rabbit_client = get_message_broker_client()
    rabbit_client.send_message(
        exchange="", routing_key="text_print", body=json.dumps(text)
    )
    return {"status": "complete"}


@prints.route("/stream", methods=['POST'])
def stream_print():
    """
    Stream text to printer line-by-line without auto-cutting.

    Single message:
        POST { "text": "Hello world" } - prints a line
        POST { "cut": true } - cuts the paper

    Batch with delay:
        POST {
            "messages": [
                { "text": "Line 1" },
                { "text": "Line 2" },
                { "cut": true }
            ],
            "delay": 2
        }
    """
    data = request.get_json()
    rabbit_client = get_message_broker_client()
    time.sleep(10)
    # Batch mode: send each message individually with delay between
    if "messages" in data:
        messages = data.get("messages", [])
        delay = data.get("delay", 0)
        count = 0

        for i, msg in enumerate(messages):
            if msg.get("cut"):
                message = {"type": "cut"}
            else:
                text = msg.get("text", "")
                message = {"type": "line", "text": text + "\n\n\n\n\n\n\n\n"}

            print(message)
            rabbit_client.send_message(
                exchange="", routing_key="stream_print", body=json.dumps(message)
            )
            count += 1

            # Delay between messages (but not after the last one)
            if delay > 0 and i < len(messages) - 1:
                time.sleep(delay)

        return {"status": "sent", "count": count}

    # Single message mode (original behavior)
    if data.get("cut"):
        message = {"type": "cut"}
    else:
        text = data.get("text", "")
        message = {"type": "line", "text": text + "\n\n\n\n\n\n\n\n"}
    print(message)
    rabbit_client.send_message(
        exchange="", routing_key="stream_print", body=json.dumps(message)
    )
    return {"status": "sent"}
