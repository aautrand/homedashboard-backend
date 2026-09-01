import os

from flask import Flask, request

from dashboard.src.ai.clients import ollama_client, whisper_client
from dashboard.src.db import create_session
from dashboard.src.message_broker.clients.base import get_message_broker_client
from dashboard.src.utils.helpers import env_flag, get_version
from dashboard.src.utils.logging import setup_logging


def setup_config(app):
    app.config["APPLE_USER"] = os.getenv("APPLE_USER")
    app.config["APPLE_DASHBOARD_SECRET"] = os.getenv("APPLE_DASHBOARD_SECRET")
    app.config["CALDAV_ICLOUD_URL"] = os.getenv("CALDAV_ICLOUD_URL")
    app.config["MAIN_CALENDAR"] = os.getenv("MAIN_CALENDAR")
    app.config["RABBITMQ_HOST"] = os.getenv("RABBITMQ_HOST")
    app.config["RABBITMQ_USER"] = os.getenv("RABBITMQ_USER")
    app.config["RABBITMQ_PASSWORD"] = os.getenv("RABBITMQ_PASSWORD")
    app.config["LAT_LONG"] = os.getenv("LAT_LONG")
    app.config["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY") or os.getenv(
        "ANTHROPIC_KEY"
    )
    app.config["ANTHROPIC_WORKSPACE_ID"] = os.getenv("ANTHROPIC_WORKSPACE_ID")
    app.config["WHISPER_URL"] = os.getenv("WHISPER_URL", whisper_client.DEFAULT_URL)
    app.config["OLLAMA_HOST"] = os.getenv("OLLAMA_HOST", ollama_client.DEFAULT_HOST)
    app.config["WHISPER_ENABLED"] = env_flag("WHISPER_ENABLED", default=True)
    app.config["DB_HOST"] = os.getenv("DB_HOST")
    app.config["DB_PORT"] = os.getenv("DB_PORT")
    app.config["DB_USER"] = os.getenv("DB_USER")
    app.config["DB_PASSWORD"] = os.getenv("DB_PASSWORD")
    app.config["DB_NAME"] = os.getenv("DB_NAME")
    app.config["OPEN_WEATHER_API_KEY"] = os.getenv("OPEN_WEATHER_API_KEY")


def register_blueprints(app):
    from dashboard.src.ai import ai
    from dashboard.src.audio import audio
    from dashboard.src.calendars import calendar
    from dashboard.src.data import data
    from dashboard.src.learning import learning
    from dashboard.src.prints import prints
    from dashboard.src.quotes import quotes
    from dashboard.src.tasks import tasks
    from dashboard.src.weather import weather

    app.register_blueprint(weather)
    app.register_blueprint(calendar)
    app.register_blueprint(tasks)
    app.register_blueprint(ai)
    app.register_blueprint(audio)
    app.register_blueprint(learning)
    app.register_blueprint(prints)
    app.register_blueprint(data)
    app.register_blueprint(quotes)

    from dashboard.src.audio import sock

    sock.init_app(app)


def setup_message_broker(app):
    with app.app_context():
        message_broker_client = get_message_broker_client()
        app.config["message_broker_client"] = message_broker_client


def configure_db(app):

    @app.before_request
    def start_session():
        session = create_session(app)
        request.db = session

    @app.teardown_request
    def remove_session(exception):
        db = getattr(request, "db", None)
        if exception:
            db.rollback()
        else:
            db.commit()

        db.close()


def create_app():

    app = Flask(__name__)

    @app.route("/info")
    def info():
        app_info = {"version": get_version()}

        return app_info

    # Configuration
    setup_config(app)
    setup_logging()
    setup_message_broker(app)
    configure_db(app)
    # Register blueprints
    register_blueprints(app)

    return app
