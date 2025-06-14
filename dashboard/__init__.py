import logging
import os
from pathlib import Path

from flask import Flask

from dashboard.src.utils.Loggers import IgnoreIcalFilter
from dashboard.src.weather.clients.noaa_client import NOAAWeatherClient


def setup_config(app):

    app.config["WEATHER_CLIENT"] = NOAAWeatherClient()
    app.config["APPLE_USER"] = os.getenv("APPLE_USER")
    app.config["APPLE_DASHBOARD_SECRET"] = os.getenv("APPLE_DASHBOARD_SECRET")
    app.config["CALDAV_ICLOUD_URL"] = os.getenv("CALDAV_ICLOUD_URL")
    app.config["RABBIT_URL"] = os.getenv("RABBIT_URL")


def setup_logging():
    logging.getLogger().addFilter(IgnoreIcalFilter())


def register_blueprints(app):
    from dashboard.src.calendar import calendar
    from dashboard.src.weather import weather

    app.register_blueprint(weather)
    app.register_blueprint(calendar)


def create_app():

    app = Flask(__name__)

    # Configuration
    setup_config(app)

    # Register blueprints
    register_blueprints(app)

    return app
