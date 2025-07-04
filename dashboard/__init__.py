import logging
import os

from flask import Flask

from dashboard.src.message_broker.clients.base import get_message_broker_client
from dashboard.src.utils.Loggers import IgnoreIcalFilter


def setup_config(app):
    app.config["APPLE_USER"] = os.getenv("APPLE_USER")
    app.config["APPLE_DASHBOARD_SECRET"] = os.getenv("APPLE_DASHBOARD_SECRET")
    app.config["CALDAV_ICLOUD_URL"] = os.getenv("CALDAV_ICLOUD_URL")
    app.config["RABBIT_URL"] = os.getenv("RABBIT_URL")
    app.config["MAIN_CALENDAR"] = os.getenv("MAIN_CALENDAR")
    app.config["RABBITMQ_HOST"] = os.getenv("RABBITMQ_HOST")
    app.config["LAT_LONG"] = os.getenv("LAT_LONG")
    app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


def setup_logging():
    logging.getLogger().addFilter(IgnoreIcalFilter())


def register_blueprints(app):
    from dashboard.src.ai import ai
    from dashboard.src.calendar import calendar
    from dashboard.src.tasks import tasks
    from dashboard.src.weather import weather

    app.register_blueprint(weather)
    app.register_blueprint(calendar)
    app.register_blueprint(tasks)
    app.register_blueprint(ai)


def setup_message_broker(app):
    message_broker_client = get_message_broker_client()
    app.config["message_broker_client"] = message_broker_client


def create_app():

    app = Flask(__name__)

    # Configuration
    setup_config(app)

    # Register blueprints
    register_blueprints(app)

    return app
