import json
import os
import re
import uuid
from logging import getLogger

from flask import Blueprint, current_app, request

from dashboard.src.ai.agents.math_agent import MathAgent
from dashboard.src.ai.clients.openai_client import OpenAIClient
from dashboard.src.prints.orchestration import print_tasks
from dashboard.src.prints.print_manager import PrintManager
from dashboard.src.prints.receipts.formatter import MathPrinterFormatter
from dashboard.src.storage import get_storage_client
from dashboard.src.utils.helpers import get_hash, latex_to_png

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


def convert_latex_to_images(problems: list) -> list:
    """
    Convert LaTeX elements in problems to images stored in MinIO.

    For each element with kind="latex", converts the LaTeX to a PNG image,
    uploads it to MinIO in the "problems" bucket, and replaces the element
    with an image reference containing the URL.

    Args:
        problems: List of problem dictionaries with elements

    Returns:
        Modified problems list with LaTeX elements converted to image references
    """
    storage_client = get_storage_client("minio")

    for problem in problems:
        for element in problem.get("elements", []):
            if element.get("kind") == "latex":
                latex_content = element["content"]
                logger.info(f"Converting LaTeX to image: {latex_content[:50]}...")

                # Normalize LaTeX to strip $...$ and \(...\) delimiters
                latex_content = normalize(latex_content)
                logger.info(f"Normalized LaTeX: {latex_content[:50]}...")

                # Generate unique filename
                unique_id = uuid.uuid4().hex
                filename = f"{unique_id}.png"
                local_path = os.path.join("/tmp", filename)

                try:
                    # Convert LaTeX to PNG
                    latex_to_png(
                        latex_content, local_path, fontsize=12, dpi=300, pad_inches=0.05
                    )
                    logger.info(
                        f"Created PNG at {local_path}, exists: {os.path.exists(local_path)}"
                    )

                    # Verify file was created before uploading
                    if not os.path.exists(local_path):
                        logger.error(f"Failed to create PNG file at {local_path}")
                        continue

                    # Upload to MinIO in "problems" bucket
                    image_url = storage_client.upload_file(
                        local_path, filename, bucket="problems"
                    )
                    logger.info(f"Uploaded to MinIO: {image_url}")

                    # Update element to be an image reference (store path, not full URL)
                    element["kind"] = "image"
                    element["content"] = f"problems/{filename}"

                except Exception as e:
                    logger.error(f"Failed to convert LaTeX to image: {e}")
                    # Keep original latex element if conversion fails
                    continue

                finally:
                    # Clean up temp file
                    if os.path.exists(local_path):
                        os.remove(local_path)

    return problems


@tasks.route("/print")
def current():
    logger.info("Printing tasks")
    tasks_list = print_tasks()
    rabbit_client = current_app.config["message_broker_client"]
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

    # Convert LaTeX elements to images stored in MinIO
    processed_problems = convert_latex_to_images(raw_problems["problems"])

    return {"status": "successful", "problems": processed_problems}
