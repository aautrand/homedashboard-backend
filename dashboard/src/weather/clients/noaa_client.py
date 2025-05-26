import requests
from dashboard.src.weather.clients.base import WeatherClient
from dashboard.src.weather.clients.models.mappers.noaa_mapper import NOAAObservationMapper


class NOAAWeatherClient(WeatherClient):
    BASE_URL = 'https://api.weather.gov'
    mapper = NOAAObservationMapper()

    def fetch_raw_observation(self, location: str) -> dict:
        pts = requests.get(f"{self.BASE_URL}/points/{location}").json()
        station = pts["properties"]["radarStation"]
        return requests.get(
            f"{self.BASE_URL}/stations/{station}/observations/latest"
        ).json()
