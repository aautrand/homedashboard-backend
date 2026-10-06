from unittest.mock import patch

import pytest
from flask import Flask

from dashboard.src.recipes import recipes
from dashboard.src.recipes.models import Ingredient, Recipe, RecipeSummary, Step

SERVICE = "dashboard.src.recipes.get_recipe_service"


@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(recipes)
    return app.test_client()


def make_recipe():
    return Recipe(
        id=7,
        name="Lasagna",
        steps=[Step(instruction="Bake", ingredients=[Ingredient(food="pasta")])],
    )


class TestListRecipes:
    @patch(SERVICE)
    def test_lists_with_query(self, mock_service, client):
        mock_service.return_value.search_recipes.return_value = [
            RecipeSummary(id=7, name="Lasagna")
        ]

        response = client.get("/recipes?query=lasag")

        assert response.status_code == 200
        assert response.get_json()[0]["name"] == "Lasagna"
        mock_service.return_value.search_recipes.assert_called_once_with("lasag")

    @patch(SERVICE)
    def test_tandoor_down_returns_502(self, mock_service, client):
        mock_service.return_value.search_recipes.side_effect = Exception("down")

        assert client.get("/recipes").status_code == 502


class TestGetRecipe:
    @patch(SERVICE)
    def test_returns_recipe(self, mock_service, client):
        mock_service.return_value.get_recipe.return_value = make_recipe()

        response = client.get("/recipes/7")

        assert response.status_code == 200
        assert response.get_json()["ingredients"] == ["pasta"]

    @patch(SERVICE)
    def test_not_found(self, mock_service, client):
        mock_service.return_value.get_recipe.return_value = None

        assert client.get("/recipes/99").status_code == 404


class TestPrintIngredients:
    @patch(SERVICE)
    def test_prints(self, mock_service, client):
        mock_service.return_value.print_ingredients.return_value = make_recipe()

        response = client.post("/recipes/7/print-ingredients")

        assert response.status_code == 200
        assert response.get_json() == {
            "status": "ok",
            "recipe": "Lasagna",
            "ingredient_count": 1,
        }

    @patch(SERVICE)
    def test_not_found(self, mock_service, client):
        mock_service.return_value.print_ingredients.return_value = None

        assert client.post("/recipes/99/print-ingredients").status_code == 404
