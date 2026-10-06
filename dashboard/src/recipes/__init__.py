from logging import getLogger

from flask import Blueprint, jsonify, request

from dashboard.src.recipes.recipe_service import get_recipe_service

logger = getLogger(__name__)

recipes = Blueprint("recipes", __name__, url_prefix="/recipes")


@recipes.route("", methods=["GET"])
def list_recipes():
    """All recipes from Tandoor, or those matching ?query= (fuzzy, by name)."""
    try:
        summaries = get_recipe_service().search_recipes(request.args.get("query"))
    except Exception as e:
        logger.error(f"Failed to list recipes: {e}")
        return jsonify({"error": "Failed to reach the recipe server"}), 502

    return jsonify([summary.to_dict() for summary in summaries])


@recipes.route("/<int:recipe_id>", methods=["GET"])
def get_recipe(recipe_id):
    try:
        recipe = get_recipe_service().get_recipe(recipe_id)
    except Exception as e:
        logger.error(f"Failed to fetch recipe {recipe_id}: {e}")
        return jsonify({"error": "Failed to reach the recipe server"}), 502

    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404

    return jsonify(recipe.to_dict())


@recipes.route("/<int:recipe_id>/print-ingredients", methods=["POST"])
def print_ingredients(recipe_id):
    try:
        recipe = get_recipe_service().print_ingredients(recipe_id)
    except Exception as e:
        logger.error(f"Failed to print ingredients for recipe {recipe_id}: {e}")
        return jsonify({"error": "Failed to print ingredients"}), 502

    if not recipe:
        return jsonify({"error": "Recipe not found"}), 404

    return jsonify(
        {
            "status": "ok",
            "recipe": recipe.name,
            "ingredient_count": len(recipe.ingredients),
        }
    )
