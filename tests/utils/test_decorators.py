import pytest
from flask import Flask, jsonify


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True

    from dashboard.src.utils.decorators import requires_service

    @app.route("/guarded")
    @requires_service("WHISPER_ENABLED", "Transcription")
    def guarded():
        return jsonify({"status": "ran"})

    return app


class TestRequiresService:
    """Tests for the requires_service route guard."""

    def test_runs_when_enabled(self, app):
        """Test the view executes normally when the flag is on."""
        app.config["WHISPER_ENABLED"] = True

        response = app.test_client().get("/guarded")

        assert response.status_code == 200
        assert response.get_json() == {"status": "ran"}

    def test_returns_503_when_disabled(self, app):
        """Test a parked service answers 503, not a connection error."""
        app.config["WHISPER_ENABLED"] = False

        response = app.test_client().get("/guarded")

        assert response.status_code == 503
        assert response.get_json() == {
            "error": "Transcription is currently unavailable"
        }

    def test_enabled_when_config_missing(self, app):
        """Test an absent flag is treated as enabled."""
        app.config.pop("WHISPER_ENABLED", None)

        assert app.test_client().get("/guarded").status_code == 200

    def test_preserves_view_name(self, app):
        """Test functools.wraps keeps the endpoint name for url routing."""
        assert "guarded" in app.view_functions
