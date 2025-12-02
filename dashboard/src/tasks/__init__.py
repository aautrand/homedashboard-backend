import json
import re
from logging import getLogger

from flask import Blueprint, request

from dashboard.src.ai.agents.math_agent import MathAgent
from dashboard.src.ai.clients.openai_client import OpenAIClient
from dashboard.src.message_broker.clients.base import get_message_broker_client
from dashboard.src.prints.print_manager import PrintManager
from dashboard.src.prints.receipts.formatter import MathPrinterFormatter
from dashboard.src.utils.helpers import get_hash

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


@tasks.route("/math-problems")
def math_problems():
    print_manager = PrintManager()
    data = request.get_json()
    prompt = data.get("prompt", [])

    openai_client = OpenAIClient()
    math_agent = MathAgent(client=openai_client)
    raw_problems = math_agent.generate_problems(prompt)
    raw_problems["problem_hash"] = get_hash(raw_problems)

    problem_formatter = MathPrinterFormatter()
    print_formatted_problems = problem_formatter.process(raw_problems)

    print_manager.print_problems(print_formatted_problems)

    return {"status": "successful", "problems": raw_problems["problems"]}
