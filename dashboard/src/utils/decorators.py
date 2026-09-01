import functools

from flask import current_app, jsonify


def requires_service(config_key: str, service_name: str):
    """Short-circuit a route with 503 while a backing service is switched off.

    Lets an endpoint be parked without unregistering it, so callers get a
    truthful "temporarily unavailable" instead of a connection error from
    whatever is down. Missing config counts as enabled.

    Args:
        config_key: Boolean app config key guarding the route.
        service_name: Name used in the error message.
    """

    def decorator(view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            if not current_app.config.get(config_key, True):
                return (
                    jsonify({"error": f"{service_name} is currently unavailable"}),
                    503,
                )
            return view(*args, **kwargs)

        return wrapper

    return decorator
