from abc import ABC, abstractmethod
from typing import Dict
from dashboard.src.weather.clients.models.observation import Observation
from dashboard.src.weather.clients.models.mappers.base import ObservationMapper

class WeatherClient(ABC):
    mapper: ObservationMapper

    @abstractmethod
    def fetch_raw_observation(self, location: str) -> Dict:
        """Fetch the raw JSON from whatever API."""
        ...

    def get_current_weather(self, location: str) -> Observation:
        raw = self.fetch_raw_observation(location)
        return self.mapper.map(raw)


# optional: a factory to pick your client by name
def get_weather_client(source: str="noaa") -> WeatherClient:
    if source == 'noaa':
        from .noaa_client import NOAAWeatherClient
        return NOAAWeatherClient()
    else:
        raise ValueError(f"Unknown source {source!r}")
