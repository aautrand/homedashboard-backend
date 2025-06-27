from flask import Blueprint

from dashboard.src.message_broker.clients.base import get_message_broker_client
from dashboard.src.prints.print_manager import PrintManager

tasks = Blueprint("tasks", __name__, url_prefix="/tasks")


@tasks.route("/print")
def current():
    print_manager = PrintManager()
    tasks = print_manager.print_tasks()
    rabbit_client = get_message_broker_client()
    rabbit_client.send_message(exchange="", routing_key="hello", body=tasks)
    return {"status": "ok"}
