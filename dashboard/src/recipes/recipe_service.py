from typing import Optional

from dashboard.src.prints.print_manager import PrintManager
from dashboard.src.prints.printer import ReceiptPrinter, get_receipt_printer
from dashboard.src.recipes.clients import get_recipe_client
from dashboard.src.recipes.models import Recipe, RecipeSummary


class RecipeService:
    """Recipe use cases shared by the /recipes routes and the home agent."""

    def __init__(self, client, printer: ReceiptPrinter):
        """
        Args:
            client: Recipe source exposing list_recipes() and get_recipe().
            printer: Receipt printer for ingredient lists.
        """
        self.client = client
        self.printer = printer

    def search_recipes(self, query: Optional[str] = None) -> list[RecipeSummary]:
        """All recipes, or those whose name matches `query`."""
        return self.client.list_recipes(query or None)

    def get_recipe(self, recipe_id: int) -> Optional[Recipe]:
        return self.client.get_recipe(recipe_id)

    def print_ingredients(self, recipe_id: int) -> Optional[Recipe]:
        """Print a recipe's ingredient list as a checklist.

        Returns:
            The recipe, or None if it doesn't exist (nothing is printed).
        """
        recipe = self.client.get_recipe(recipe_id)
        if recipe:
            self.printer.print_receipt(PrintManager.print_ingredients(recipe))
        return recipe


def get_recipe_service() -> RecipeService:
    """Build the service wired to Tandoor and the printer. Requires an app context."""
    return RecipeService(get_recipe_client(), get_receipt_printer())
