"""Tools that expose backend services to the home agent.

Each tool is an adapter: it calls one service method and turns the result into
text for the model. Business rules (what completing a todo does, how calendar
data is refreshed, how quotes are matched) belong to the managers and
services, so the dashboard's HTTP routes and the agent behave the same way.
"""

import json
from datetime import date
from typing import Optional

from langchain_core.tools import BaseTool, tool

from dashboard.src.ai.agents.home_services import HomeServices

# Tools that put something on paper themselves. The voice pipeline skips the
# automatic reply receipt after any of these, so one request prints once.
PRINTING_TOOLS = frozenset({"print_text", "print_recipe_ingredients"})


def _to_json(value) -> str:
    return json.dumps(value, default=str)


def build_home_tools(services: HomeServices) -> list[BaseTool]:
    """Bind the agent's tools to a set of services."""

    @tool
    def list_todos() -> str:
        """List the user's open todos with their IDs.

        Call this before completing a todo, then pick the ID whose title best
        matches what the user described.
        """
        todos = services.todos.get_active_todos()
        return _to_json([{"id": todo.id, "title": todo.title} for todo in todos])

    @tool
    def add_todo(title: str) -> str:
        """Add a todo to the user's list."""
        todo = services.todos.add_todo(title=title)
        return _to_json({"id": todo.id, "title": todo.title})

    @tool
    def complete_todo(todo_id: int) -> str:
        """Mark a todo as done by ID."""
        todo = services.todos.complete_todo(todo_id)
        if not todo:
            return f"No todo with ID {todo_id}."
        return _to_json({"id": todo.id, "title": todo.title, "done": True})

    @tool
    def get_calendar_events(day: date) -> str:
        """Get the user's calendar events for one day (ISO date, e.g. 2026-10-07)."""
        events = services.calendar.get_synced_events_for_date(day)
        return _to_json(
            [
                {
                    "summary": event.summary,
                    "calendar": event.calendar,
                    "start": event.start_time,
                    "end": event.end_time,
                }
                for event in events
            ]
        )

    @tool
    def get_weather() -> str:
        """Get current conditions and today's forecast for the user's home.

        Temperatures are in Celsius.
        """
        return services.weather.get_weather().to_json()

    @tool
    def search_quotes(query: str) -> str:
        """Search the quote pool by words in the text or the author's name."""
        quotes = services.quotes.search_quotes(query)
        return _to_json(
            [
                {
                    "id": quote.id,
                    "text": quote.text,
                    "author": quote.author,
                    "pinned": quote.pinned,
                }
                for quote in quotes
            ]
        )

    @tool
    def add_quote(text: str, author: Optional[str] = None) -> str:
        """Add a quote to the pool printed on the daily receipt."""
        quote = services.quotes.add_quote(text=text, author=author)
        return _to_json({"id": quote.id, "text": quote.text, "author": quote.author})

    @tool
    def pin_quote(quote_id: int) -> str:
        """Pin a quote by ID so it prints on every daily receipt until changed.

        Only one quote can be pinned; pinning replaces the previous one.
        """
        quote = services.quotes.pin_quote(quote_id)
        if not quote:
            return f"No quote with ID {quote_id}."
        return _to_json({"id": quote.id, "text": quote.text, "pinned": True})

    @tool
    def create_flashcard(title: str, content: str) -> str:
        """Create one study flashcard. `title` is the prompt, `content` the answer.

        Call once per card when the user asks for several.
        """
        card = services.cards.add_card(title=title, content=content)
        return _to_json({"id": card.id, "title": card.title})

    @tool
    def search_recipes(query: Optional[str] = None) -> str:
        """Find recipes in the user's recipe collection by name.

        Leave `query` empty to list every recipe. Use this to find a recipe's
        ID before getting or printing it.
        """
        recipes = services.recipes.search_recipes(query)
        return _to_json([{"id": recipe.id, "name": recipe.name} for recipe in recipes])

    @tool
    def get_recipe(recipe_id: int) -> str:
        """Get one recipe by ID: servings, times, ingredients and steps."""
        recipe = services.recipes.get_recipe(recipe_id)
        if not recipe:
            return f"No recipe with ID {recipe_id}."
        return _to_json(
            {
                "id": recipe.id,
                "name": recipe.name,
                "servings": recipe.servings,
                "working_minutes": recipe.working_time,
                "waiting_minutes": recipe.waiting_time,
                "ingredients": [i.display() for i in recipe.ingredients],
                "steps": [step.instruction for step in recipe.steps],
            }
        )

    @tool
    def print_recipe_ingredients(recipe_id: int) -> str:
        """Print a recipe's ingredient list as a checklist on the receipt printer.

        Only call this when the user asks to print ingredients.
        """
        recipe = services.recipes.print_ingredients(recipe_id)
        if not recipe:
            return f"No recipe with ID {recipe_id}."
        return f"Printed {len(recipe.ingredients)} ingredients for {recipe.name}."

    @tool
    def print_text(text: str) -> str:
        """Print text on the receipt printer (48 characters wide).

        Only call this when the user explicitly asks to print something.
        """
        services.printer.print_text(text)
        return "Printed."

    @tool
    def skip_reply_print() -> str:
        """Stop your reply to this request from being printed.

        Call this when the user says not to print ("don't print anything",
        "no printout"). Your reply is still returned to the device, just not
        printed.
        """
        # No backend call: the voice pipeline owns reply printing and checks
        # for this tool in the agent's used_tools, as it does for print_text.
        return "Your reply will not be printed."

    return [
        list_todos,
        add_todo,
        complete_todo,
        get_calendar_events,
        get_weather,
        search_quotes,
        add_quote,
        pin_quote,
        create_flashcard,
        search_recipes,
        get_recipe,
        print_recipe_ingredients,
        print_text,
        skip_reply_print,
    ]
