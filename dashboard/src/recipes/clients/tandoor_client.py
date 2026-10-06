from typing import Optional

import requests

from dashboard.src.recipes.models import Ingredient, Recipe, RecipeSummary, Step

DEFAULT_URL = "http://localhost:8040"

DEFAULT_TIMEOUT = 15

# Tandoor's list endpoint pages its results; 100 keeps "all recipes" to a few
# requests for a household-sized collection.
PAGE_SIZE = 100


class TandoorNotFound(Exception):
    """The requested object does not exist on the Tandoor server."""


class TandoorClient:
    """Read-only client for a Tandoor Recipes server (REST API, v2).

    Talks to the API directly with `requests`, like the other external
    clients, and maps Tandoor's JSON onto the dashboard's recipe models so
    nothing outside this module depends on Tandoor's field names.
    """

    def __init__(self, base_url: str, token: str, timeout: int = DEFAULT_TIMEOUT):
        """
        Args:
            base_url: Server root, e.g. "http://localhost:8040".
            token: API token from Tandoor's Settings → API.
            timeout: Seconds to wait per request.
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def list_recipes(self, query: Optional[str] = None) -> list[RecipeSummary]:
        """Every recipe, or those whose name fuzzily matches `query`."""
        summaries = []
        page = 1
        while True:
            params = {"page": page, "page_size": PAGE_SIZE}
            if query:
                params["query"] = query
            body = self._get("/api/recipe/", params)
            summaries.extend(_to_summary(item) for item in body["results"])
            if not body.get("next"):
                return summaries
            page += 1

    def get_recipe(self, recipe_id: int) -> Optional[Recipe]:
        """One recipe with its steps and ingredients, or None if it doesn't exist."""
        try:
            return _to_recipe(self._get(f"/api/recipe/{recipe_id}/"))
        except TandoorNotFound:
            return None

    def _get(self, path: str, params: dict = None) -> dict:
        try:
            response = requests.get(
                f"{self.base_url}{path}",
                headers={"Authorization": f"Bearer {self.token}"},
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise TandoorNotFound(path) from e
            # Tandoor explains 401/403 in the body (bad token vs. no space).
            raise Exception(
                f"Tandoor request failed ({e.response.status_code}): {e.response.text}"
            ) from e
        except requests.RequestException as e:
            raise Exception(f"Failed to reach Tandoor at {self.base_url}: {e}") from e
        return response.json()


def _to_summary(data: dict) -> RecipeSummary:
    return RecipeSummary(
        id=data["id"],
        name=data["name"],
        description=data.get("description"),
        servings=data.get("servings") or 0,
        servings_text=data.get("servings_text") or "",
        working_time=data.get("working_time") or 0,
        waiting_time=data.get("waiting_time") or 0,
    )


def _to_recipe(data: dict) -> Recipe:
    steps = sorted(data.get("steps", []), key=lambda step: step.get("order", 0))
    return Recipe(
        id=data["id"],
        name=data["name"],
        description=data.get("description"),
        servings=data.get("servings") or 0,
        servings_text=data.get("servings_text") or "",
        working_time=data.get("working_time") or 0,
        waiting_time=data.get("waiting_time") or 0,
        source_url=data.get("source_url"),
        steps=[_to_step(step) for step in steps],
    )


def _to_step(data: dict) -> Step:
    ingredients = sorted(
        data.get("ingredients", []), key=lambda ingredient: ingredient.get("order", 0)
    )
    return Step(
        name=data.get("name") or "",
        instruction=data.get("instruction") or "",
        ingredients=[_to_ingredient(ingredient) for ingredient in ingredients],
    )


def _to_ingredient(data: dict) -> Ingredient:
    food = data.get("food") or {}
    unit = data.get("unit") or {}
    return Ingredient(
        # Header rows have no food; their title is in `note`.
        food=food.get("name") or data.get("note") or "",
        amount=data.get("amount") or 0,
        unit=unit.get("name"),
        note=None if data.get("is_header") else data.get("note") or None,
        is_header=bool(data.get("is_header")),
        no_amount=bool(data.get("no_amount")),
    )
