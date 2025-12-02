import json
import time
from flask import Blueprint, request

from dashboard import get_message_broker_client
from prints.print_manager import PrintManager

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
