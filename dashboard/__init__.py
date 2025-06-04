from flask import Flask
from dashboard.src.weather.clients.noaa_client import NOAAWeatherClient

def register_blueprints(app):
    from dashboard.src.weather import bp
    app.register_blueprint(bp)

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config["WEATHER_CLIENT"] = NOAAWeatherClient()
    # TODO Find out what happens if I register the blueprint before setting the config
    register_blueprints(app)

    return app