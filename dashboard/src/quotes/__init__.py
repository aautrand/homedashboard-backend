from logging import getLogger

from flask import Blueprint, jsonify, request

from dashboard.src.quotes.quote_manager import QuoteManager

logger = getLogger(__name__)

quotes = Blueprint("quotes", __name__, url_prefix="/quotes")

# Fields a client is allowed to change through a plain update. `pinned` is
# deliberately excluded so pinning always goes through /quotes/pinned, which
# guarantees only one quote is ever pinned.
UPDATABLE_FIELDS = {"text", "author", "active"}


@quotes.route("", methods=["POST"])
def create_quote():
    data = request.get_json()

    if not data or "text" not in data:
        return jsonify({"error": "Missing required field: text"}), 400

    quote_manager = QuoteManager(request.db)
    quote = quote_manager.add_quote(
        text=data["text"],
        author=data.get("author"),
        active=data.get("active", True),
    )

    return jsonify(quote.to_dict()), 201


@quotes.route("", methods=["GET"])
def get_quotes():
    quote_manager = QuoteManager(request.db)

    active_param = request.args.get("active")
    if active_param is not None:
        active_lower = active_param.lower()
        if active_lower not in ("true", "false"):
            return (
                jsonify({"error": "Invalid value for 'active'. Use 'true' or 'false'"}),
                400,
            )
        quote_list = quote_manager.get_quotes_by_status(active_lower == "true")
    else:
        quote_list = quote_manager.get_all_quotes()

    return jsonify([quote.to_dict() for quote in quote_list])


@quotes.route("/pinned", methods=["GET"])
def get_pinned_quote():
    quote_manager = QuoteManager(request.db)
    quote = quote_manager.get_pinned_quote()

    if not quote:
        return jsonify({"error": "No quote is currently pinned"}), 404

    return jsonify(quote.to_dict())


@quotes.route("/pinned", methods=["PUT"])
def set_pinned_quote():
    data = request.get_json()

    if not data or "quote_id" not in data:
        return jsonify({"error": "Missing required field: quote_id"}), 400

    quote_manager = QuoteManager(request.db)
    quote = quote_manager.pin_quote(data["quote_id"])

    if not quote:
        return jsonify({"error": "Quote not found"}), 404

    logger.info(f"Pinned quote {quote.id}")
    return jsonify(quote.to_dict())


@quotes.route("/pinned/cycle", methods=["POST"])
def cycle_pinned_quote():
    quote_manager = QuoteManager(request.db)
    quote = quote_manager.cycle_pinned_quote()

    if not quote:
        return jsonify({"error": "No quotes available to pin"}), 404

    logger.info(f"Cycled pinned quote to {quote.id}")
    return jsonify(quote.to_dict())


@quotes.route("/pinned", methods=["DELETE"])
def clear_pinned_quote():
    quote_manager = QuoteManager(request.db)
    quote = quote_manager.unpin_quote()

    if not quote:
        return jsonify({"error": "No quote is currently pinned"}), 404

    return jsonify({"message": "Quote unpinned successfully"})


@quotes.route("/reset-rotation", methods=["POST"])
def reset_rotation():
    quote_manager = QuoteManager(request.db)
    count = quote_manager.reset_rotation()

    return jsonify({"message": f"Reset rotation for {count} quotes", "count": count})


@quotes.route("/<int:quote_id>", methods=["GET"])
def get_quote(quote_id):
    quote_manager = QuoteManager(request.db)
    quote = quote_manager.get_quote(quote_id)

    if not quote:
        return jsonify({"error": "Quote not found"}), 404

    return jsonify(quote.to_dict())


@quotes.route("/<int:quote_id>", methods=["PUT"])
def update_quote(quote_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    updates = {key: value for key, value in data.items() if key in UPDATABLE_FIELDS}
    if not updates:
        return (
            jsonify(
                {
                    "error": "No updatable fields provided. "
                    f"Allowed: {', '.join(sorted(UPDATABLE_FIELDS))}"
                }
            ),
            400,
        )

    quote_manager = QuoteManager(request.db)
    quote = quote_manager.update_quote(quote_id, **updates)

    if not quote:
        return jsonify({"error": "Quote not found"}), 404

    return jsonify(quote.to_dict())


@quotes.route("/<int:quote_id>", methods=["DELETE"])
def delete_quote(quote_id):
    quote_manager = QuoteManager(request.db)
    quote = quote_manager.delete_quote(quote_id)

    if not quote:
        return jsonify({"error": "Quote not found"}), 404

    return jsonify({"message": "Quote deleted successfully"})
