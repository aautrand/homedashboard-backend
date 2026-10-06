from flask import current_app


def get_recipe_client(source: str = "tandoor"):
    """Build a recipe client, wired from app config. Requires an app context."""
    if source == "tandoor":
        from .tandoor_client import TandoorClient

        return TandoorClient(
            base_url=current_app.config["TANDOOR_URL"],
            token=current_app.config["TANDOOR_API_TOKEN"],
        )
    else:
        raise ValueError(f"Unknown source {source!r}")
