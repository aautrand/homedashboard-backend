from unittest.mock import MagicMock, patch

import pytest
import requests

from dashboard.src.recipes.clients.tandoor_client import TandoorClient

GET = "dashboard.src.recipes.clients.tandoor_client.requests.get"


def _response(body, status=200):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = body
    if status >= 400:
        response.text = "detail"
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
    return response


def _page(results, next_url=None):
    return {"count": len(results), "next": next_url, "results": results}


@pytest.fixture
def client():
    return TandoorClient("http://tandoor:8040/", "tok")


class TestListRecipes:
    @patch(GET)
    def test_sends_bearer_token_and_query(self, mock_get, client):
        mock_get.return_value = _response(_page([{"id": 1, "name": "Lasagna"}]))

        result = client.list_recipes("lasag")

        mock_get.assert_called_once_with(
            "http://tandoor:8040/api/recipe/",
            headers={"Authorization": "Bearer tok"},
            params={"page": 1, "page_size": 100, "query": "lasag"},
            timeout=15,
        )
        assert [(r.id, r.name) for r in result] == [(1, "Lasagna")]

    @patch(GET)
    def test_follows_pages_until_next_is_empty(self, mock_get, client):
        mock_get.side_effect = [
            _response(_page([{"id": 1, "name": "A"}], next_url="http://x/?page=2")),
            _response(_page([{"id": 2, "name": "B"}])),
        ]

        result = client.list_recipes()

        assert [r.id for r in result] == [1, 2]
        assert mock_get.call_args_list[1].kwargs["params"] == {
            "page": 2,
            "page_size": 100,
        }

    @patch(GET)
    def test_auth_error_includes_status(self, mock_get, client):
        mock_get.return_value = _response({}, status=401)

        with pytest.raises(Exception, match=r"Tandoor request failed \(401\)"):
            client.list_recipes()

    @patch(GET)
    def test_connection_error(self, mock_get, client):
        mock_get.side_effect = requests.ConnectionError("refused")

        with pytest.raises(Exception, match="Failed to reach Tandoor"):
            client.list_recipes()


TANDOOR_RECIPE = {
    "id": 7,
    "name": "Lasagna",
    "description": "Family recipe",
    "servings": 6,
    "servings_text": "portions",
    "working_time": 30,
    "waiting_time": 45,
    "source_url": None,
    "steps": [
        {
            "order": 1,
            "name": "Bake",
            "instruction": "Bake 45 minutes.",
            "ingredients": [],
        },
        {
            "order": 0,
            "name": "Sauce",
            "instruction": "Simmer the sauce.",
            "ingredients": [
                {
                    "order": 1,
                    "food": {"name": "tomatoes"},
                    "unit": {"name": "g"},
                    "amount": 800.0,
                    "note": "crushed",
                    "is_header": False,
                    "no_amount": False,
                },
                {
                    "order": 0,
                    "food": None,
                    "unit": None,
                    "amount": 0,
                    "note": "For the sauce",
                    "is_header": True,
                    "no_amount": True,
                },
                {
                    "order": 2,
                    "food": {"name": "salt"},
                    "unit": None,
                    "amount": 0,
                    "note": "",
                    "is_header": False,
                    "no_amount": True,
                },
            ],
        },
    ],
}


class TestGetRecipe:
    @patch(GET)
    def test_maps_steps_and_ingredients_in_order(self, mock_get, client):
        mock_get.return_value = _response(TANDOOR_RECIPE)

        recipe = client.get_recipe(7)

        assert mock_get.call_args.args[0] == "http://tandoor:8040/api/recipe/7/"
        assert recipe.name == "Lasagna"
        assert recipe.servings == 6
        assert [s.name for s in recipe.steps] == ["Sauce", "Bake"]
        assert [i.display() for i in recipe.ingredients] == [
            "For the sauce",
            "800 g tomatoes, crushed",
            "salt",
        ]
        assert recipe.ingredients[0].is_header

    @patch(GET)
    def test_missing_recipe_returns_none(self, mock_get, client):
        mock_get.return_value = _response({}, status=404)

        assert client.get_recipe(999) is None
