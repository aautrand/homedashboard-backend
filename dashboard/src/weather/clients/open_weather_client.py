import requests
from flask import current_app

from dashboard.src.weather.clients.base import WeatherClient


class OpenWeatherClient:
    BASE_URL = "https://api.openweathermap.org"
    API_KEY = current_app.config["OPEN_WEATHER_API_KEY"]
    CURRENT_PATH = "/data/2.5/weather"
    FORCAST_PATH = "/data/2.5/forecast"
    QUERY_STRING = {"appid": API_KEY, "units": "metric", "cnt": 8}

    def get_current_weather(self, location: str):
        lat, lon = location.replace(" ", "").split(",")
        self.QUERY_STRING["lat"] = lat
        self.QUERY_STRING["lon"] = lon

        raw_current_weather = requests.get(
            f"{self.BASE_URL}{self.CURRENT_PATH}", params=self.QUERY_STRING, timeout=10
        ).json()
        return raw_current_weather

    def get_forecast_weather(self, location: str):
        lat, lon = location.replace(" ", "").split(",")
        self.QUERY_STRING["lat"] = lat
        self.QUERY_STRING["lon"] = lon
        raw_forecast_weather = requests.get(
            f"{self.BASE_URL}{self.FORCAST_PATH}", params=self.QUERY_STRING, timeout=10
        ).json()

        return raw_forecast_weather

    def get_combined_weather(self, location):
        lat, lon = location.replace(" ", "").split(",")
        self.QUERY_STRING["lat"] = lat
        self.QUERY_STRING["lon"] = lon
        raw_forecast_weather = requests.get(
            f"{self.BASE_URL}{self.FORCAST_PATH}", params=self.QUERY_STRING, timeout=10
        ).json()

        return raw_forecast_weather
