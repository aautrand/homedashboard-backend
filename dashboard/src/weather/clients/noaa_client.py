import requests

from dashboard.src.weather.clients.base import WeatherClient
from dashboard.src.weather.clients.models.mappers.noaa_mapper import \
    NOAAObservationMapper


class NOAAWeatherClient(WeatherClient):
    BASE_URL = "https://api.weather.gov"
    mapper = NOAAObservationMapper()

    def fetch_raw_observation(self, location: str):
        pts = requests.get(f"{self.BASE_URL}/points/{location}").json()
        forecast = requests.get(pts["properties"]["forecast"]).json()

        station = pts["properties"]["radarStation"]
        observations = requests.get(
            f"{self.BASE_URL}/stations/{station}/observations/latest"
        ).json()

        return pts, forecast, observations
