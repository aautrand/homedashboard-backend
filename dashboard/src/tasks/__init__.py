import json
import re

from flask import Blueprint, request

from dashboard.src.ai.clients.openai_client import OpenAIClient
from dashboard.src.ai.prompts import math_prompt_template
from dashboard.src.message_broker.clients.base import get_message_broker_client
from dashboard.src.prints.print_manager import PrintManager
from logging import getLogger

logger = getLogger(__name__)

tasks = Blueprint("tasks", __name__, url_prefix="/tasks")


def normalize(expr: str) -> str:
    # 1) remove leading numbering like "2. "
    expr = re.sub(r"^\s*\d+\.\s*", "", expr)
    # 2) strip any dollar signs
    expr = expr.replace("$", "")
    # 3) strip surrounding \( … \) or \[ … \]
    #    regex looks for \(…\) or \[…\] at the very ends
    expr = re.sub(r"^\\\((.*)\\\)$", r"\1", expr)
    expr = re.sub(r"^\\\[(.*)\\\]$", r"\1", expr)
    return expr.strip()


@tasks.route("/print")
def current():
    logger.info("Printing tasks")
    print_manager = PrintManager()
    tasks_list = print_manager.print_tasks()
    rabbit_client = get_message_broker_client()
    rabbit_client.send_message(
        exchange="", routing_key="text_print", body=json.dumps(tasks_list)
    )
    return {"status": "ok"}


@tasks.route("/latex")
def latex_to_image():
    print_manager = PrintManager()
    data = request.get_json()
    formulas = data.get("formulas", [])  # each is e.g. "x^3 \cdot x^4"

    print_manager.print_problems(formulas)
    rabbit_client = get_message_broker_client()
    payload = {"count": len(formulas)}
    rabbit_client.send_message(
        exchange="", routing_key="image_print", body=str(payload)
    )
    return "finished"


@tasks.route("/math-problems")
def math_problems():
    print_manager = PrintManager()
    data = request.get_json()
    prompt = data.get("prompt", [])

    openai_client = OpenAIClient()
    formulas = (
        openai_client.generate_chatgpt_response("gpt-4o", math_prompt_template, prompt)
        .replace(" json", "")
        .replace("```", "")
    )
    lines = [normalize(line) for line in formulas.splitlines() if line.strip()]
    print_manager.print_problems(lines)
    rabbit_client = get_message_broker_client()
    # TODO why 127?
    payload = {"count": len(lines)}
    rabbit_client.send_message(
        exchange="", routing_key="image_print", body=str(payload)
    )
    return "finished"
