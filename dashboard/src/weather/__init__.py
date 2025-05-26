from flask import Blueprint
from dashboard.src.weather.clients.base import get_weather_client


bp = Blueprint('weather', __name__, url_prefix="/weather")


@bp.route("/current")
def current():
    weather_client = get_weather_client()
    obs = weather_client.get_current_weather("33.31,-111.66")
    return obs.to_json()