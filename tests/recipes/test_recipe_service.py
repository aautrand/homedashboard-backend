from unittest.mock import MagicMock, patch

import pytest

from dashboard.src.recipes.recipe_service import RecipeService


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def printer():
    return MagicMock()


@pytest.fixture
def service(client, printer):
    return RecipeService(client, printer)


class TestRecipeService:
    def test_search_passes_query(self, service, client):
        assert service.search_recipes("soup") is client.list_recipes.return_value
        client.list_recipes.assert_called_once_with("soup")

    def test_blank_query_lists_everything(self, service, client):
        service.search_recipes("")

        client.list_recipes.assert_called_once_with(None)

    def test_get_recipe(self, service, client):
        assert service.get_recipe(3) is client.get_recipe.return_value
        client.get_recipe.assert_called_once_with(3)

    @patch("dashboard.src.recipes.recipe_service.PrintManager")
    def test_print_ingredients(self, mock_print_manager, service, client, printer):
        recipe = client.get_recipe.return_value
        mock_print_manager.print_ingredients.return_value = {"r": 1}

        assert service.print_ingredients(3) is recipe

        mock_print_manager.print_ingredients.assert_called_once_with(recipe)
        printer.print_receipt.assert_called_once_with({"r": 1})

    def test_print_missing_recipe_prints_nothing(self, service, client, printer):
        client.get_recipe.return_value = None

        assert service.print_ingredients(3) is None
        printer.print_receipt.assert_not_called()
