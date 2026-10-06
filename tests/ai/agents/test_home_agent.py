from datetime import datetime
from unittest.mock import MagicMock

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from dashboard.src.ai.agents.home_agent import HomeAgent, build_home_agent


class ScriptedChatModel(GenericFakeChatModel):
    """Fake chat model that replays scripted replies and accepts tool binding."""

    def bind_tools(self, tools, **kwargs):
        return self


def make_todo(todo_id, title):
    todo = MagicMock()
    todo.id = todo_id
    todo.title = title
    return todo


class TestHomeAgent:
    def test_respond_returns_final_message_text(self):
        graph = MagicMock()
        graph.invoke.return_value = {"messages": [AIMessage("  All done.  ")]}

        assert HomeAgent(graph).respond("hi") == "All done."

    def test_respond_includes_current_time(self):
        graph = MagicMock()
        graph.invoke.return_value = {"messages": [AIMessage("ok")]}

        HomeAgent(graph).respond("what's on today?", now=datetime(2026, 10, 6, 8, 30))

        message = graph.invoke.call_args[0][0]["messages"][0]
        assert "Tuesday 2026-10-06 08:30" in message.content
        assert message.content.endswith("what's on today?")


class TestBuildHomeAgent:
    def test_completes_loosely_named_todo_through_service(self):
        """The model lists todos, picks one by ID, and the backend completes it."""
        services = MagicMock()
        services.todos.get_active_todos.return_value = [
            make_todo(1, "Buy 2% milk"),
            make_todo(2, "Call the plumber"),
        ]
        services.todos.complete_todo.return_value = make_todo(2, "Call the plumber")

        model = ScriptedChatModel(
            messages=iter(
                [
                    AIMessage(
                        "",
                        tool_calls=[{"name": "list_todos", "args": {}, "id": "call_1"}],
                    ),
                    AIMessage(
                        "",
                        tool_calls=[
                            {
                                "name": "complete_todo",
                                "args": {"todo_id": 2},
                                "id": "call_2",
                            }
                        ],
                    ),
                    AIMessage("Done: Call the plumber."),
                ]
            )
        )

        reply = build_home_agent(model, services).respond("mark the plumber one done")

        assert reply == "Done: Call the plumber."
        services.todos.complete_todo.assert_called_once_with(2)
