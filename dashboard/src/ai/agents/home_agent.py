"""Tool-using home assistant built on LangChain's create_agent (a LangGraph loop)."""

from datetime import datetime

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

Only print when the user explicitly asks you to print something ("print \
my todo list"); nothing else reaches the printer. Printed text is 48 \
columns wide, so keep it short and plain.

Answer in a few short lines of plain text, with no markdown. Confirm what \
you changed.\
"""


class HomeAgent:
    """Answers one request, calling backend tools as needed."""

    def __init__(self, graph):
        """
        Args:
            graph: A compiled agent graph accepting {"messages": [...]}.
        """
        self.graph = graph

    def respond(self, text: str, now: datetime = None) -> str:
        """Run the agent on one request and return its final reply.

        The current time rides along with the request rather than in the
        system prompt, so the system prompt stays cacheable.
        """
        now = now or datetime.now()
        message = HumanMessage(f"Current local time: {now:%A %Y-%m-%d %H:%M}\n\n{text}")
        result = self.graph.invoke({"messages": [message]})
        return result["messages"][-1].text.strip()


def build_home_agent(model, services: HomeServices) -> HomeAgent:
    return HomeAgent(
        create_agent(
            model, tools=build_home_tools(services), system_prompt=SYSTEM_PROMPT
        )
    )


def get_home_agent(db) -> HomeAgent:
    """Build the agent wired to app config and one DB session. Requires an app context."""
    return build_home_agent(get_chat_model(), build_home_services(db))
