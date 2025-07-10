import os

from flask import Flask, request

from dashboard.src.message_broker.clients.base import get_message_broker_client
from dashboard.src.utils.logging import setup_logging
from dashboard.src.db import create_session

def setup_config(app):
    app.config["APPLE_USER"] = os.getenv("APPLE_USER")
    app.config["APPLE_DASHBOARD_SECRET"] = os.getenv("APPLE_DASHBOARD_SECRET")
    app.config["CALDAV_ICLOUD_URL"] = os.getenv("CALDAV_ICLOUD_URL")
    app.config["RABBIT_URL"] = os.getenv("RABBIT_URL")
    app.config["MAIN_CALENDAR"] = os.getenv("MAIN_CALENDAR")
    app.config["RABBITMQ_HOST"] = os.getenv("RABBITMQ_HOST")
    app.config["LAT_LONG"] = os.getenv("LAT_LONG")
    app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    app.config["DB_HOST"] = os.getenv("DB_HOST")
    app.config["DB_PORT"] = os.getenv("DB_PORT")
    app.config["DB_USER"] = os.getenv("DB_USER")
    app.config["DB_PASSWORD"] = os.getenv("DB_PASSWORD")
    app.config["DB_NAME"] = os.getenv("DB_NAME")


def register_blueprints(app):
    from dashboard.src.ai import ai
    from dashboard.src.calendar import calendar
    from dashboard.src.tasks import tasks
    from dashboard.src.weather import weather
    from dashboard.src.learning import learning

    app.register_blueprint(weather)
    app.register_blueprint(calendar)
    app.register_blueprint(tasks)
    app.register_blueprint(ai)
    app.register_blueprint(learning)

def setup_message_broker(app):
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

    # Configuration
    setup_config(app)
    setup_logging()
    configure_db(app)
    # Register blueprints
    register_blueprints(app)

    return app
