from flask import Blueprint, current_app

from dashboard.src.weather.clients.base import get_weather_client

weather = Blueprint("weather", __name__, url_prefix="/weather")


@weather.route("/current")
def current():
    weather_client = get_weather_client()
    obs = weather_client.get_current_weather(current_app.config["LAT_LONG"])
    return obs.to_json()
