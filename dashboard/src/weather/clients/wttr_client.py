import requests

from dashboard.src.weather.clients.base import WeatherClient
from dashboard.src.weather.clients.models.mappers.noaa_mapper import \
    NOAAObservationMapper


class WTTRWeatherClient(WeatherClient):
    BASE_URL = "http://wttr.in"
    mapper = NOAAObservationMapper()

    def fetch_raw_observation(self, location: str) -> dict:
        weather = requests.get(f"{self.BASE_URL}/{location}?format=%C+%t+%W")
        return {"condition": weather.text}
