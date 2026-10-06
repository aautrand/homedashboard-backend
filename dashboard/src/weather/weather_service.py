from flask import current_app

from dashboard.src.weather.clients.base import get_weather_client
from dashboard.src.weather.clients.models.open_weather import OpenWeather


class WeatherService:
    """Current conditions plus today's forecast for one fixed location."""

    def __init__(self, client, location: str):
        """
        Args:
            client: OpenWeather client exposing get_current_weather() and
                get_forecast_weather().
            location: "lat,long" string.
        """
        self.client = client
        self.location = location

    def get_weather(self) -> OpenWeather:
        current = self.client.get_current_weather(self.location)
        forecast = self.client.get_forecast_weather(self.location)
        return OpenWeather.from_current_and_forecast(current, forecast)


def get_weather_service() -> WeatherService:
    """Build a weather service for the home location. Requires an app context."""
    return WeatherService(
        get_weather_client("open-weather"), current_app.config["LAT_LONG"]
    )
