"""Tool-using home assistant built on LangChain's create_agent (a LangGraph loop)."""

from datetime import datetime, tzinfo
from zoneinfo import ZoneInfo

from flask import current_app
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from dashboard.src.ai.agents.home_services import HomeServices, build_home_services
from dashboard.src.ai.agents.home_tools import build_home_tools
from dashboard.src.ai.clients.base import get_chat_model

SYSTEM_PROMPT = """\
You are the assistant for a home dashboard. Requests usually arrive as \
transcribed speech, so expect transcription errors and read for intent.

Use the tools to act on the user's todos, calendar, weather, quotes, \
flashcards and receipt printer. When the user refers to a todo or quote \
loosely ("the milk one"), look it up first and pick the closest match. If \
nothing matches, or two items match equally well, say so instead of guessing.

Your reply to a voice request is printed on the receipt printer \
automatically. Call print_text only when the user explicitly asks to print \
something ("print my todo list"); the reply is then not printed again. \
Printed text is 48 columns wide, so keep it short and plain.

Answer in a few short lines of plain text, with no markdown. Confirm what \
you changed.\
"""


class HomeAgent:
    """Answers one request, calling backend tools as needed."""

    def __init__(self, graph, tz: tzinfo = None):
        """
        Args:
            graph: A compiled agent graph accepting {"messages": [...]}.
            tz: Timezone the current time is reported in. None uses the
                server's local time, which is UTC inside the container.
        """
        self.graph = graph
        self.tz = tz
        self.used_tools: set[str] = set()

    def respond(self, text: str, now: datetime = None) -> str:
        """Run the agent on one request and return its final reply.

        The current time rides along with the request rather than in the
        system prompt, so the system prompt stays cacheable.
        """
        now = now or datetime.now(self.tz)
        message = HumanMessage(f"Current local time: {now:%A %Y-%m-%d %H:%M}\n\n{text}")
        result = self.graph.invoke({"messages": [message]})
        self.used_tools = {
            call["name"]
            for msg in result["messages"]
            for call in getattr(msg, "tool_calls", None) or []
        }
        return result["messages"][-1].text.strip()


def build_home_agent(model, services: HomeServices, tz: tzinfo = None) -> HomeAgent:
    return HomeAgent(
        create_agent(
            model, tools=build_home_tools(services), system_prompt=SYSTEM_PROMPT
        ),
        tz=tz,
    )


def get_local_timezone() -> tzinfo | None:
    """The TIMEZONE from app config, or None for server time. Requires an app context."""
    timezone = current_app.config.get("TIMEZONE")
    return ZoneInfo(timezone) if timezone else None


def get_home_agent(db) -> HomeAgent:
    """Build the agent wired to app config and one DB session. Requires an app context."""
    return build_home_agent(
        get_chat_model(), build_home_services(db), tz=get_local_timezone()
    )
