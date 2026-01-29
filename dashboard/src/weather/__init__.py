from flask import Blueprint, current_app

from dashboard.src.weather.clients.base import get_weather_client
from dashboard.src.weather.clients.models.open_weather import OpenWeather

weather = Blueprint("weather", __name__, url_prefix="/weather")


@weather.route("/current")
def current():
    weather_client = get_weather_client("wttr")
    obs = weather_client.fetch_raw_observation(current_app.config["LAT_LONG"])
    return obs


@weather.route("/open-weather")
def open_weather():
    weather_client = get_weather_client("open-weather")
    current_weather = weather_client.get_current_weather(current_app.config["LAT_LONG"])
    forecast_weather = weather_client.get_forecast_weather(
        current_app.config["LAT_LONG"]
    )
    combined = OpenWeather.from_current_and_forecast(current_weather, forecast_weather)
    return combined.to_json()
