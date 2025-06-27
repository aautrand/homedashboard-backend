from abc import ABC, abstractmethod
from typing import Dict

from dashboard.src.weather.clients.models.mappers.base import ObservationMapper
from dashboard.src.weather.clients.models.observation import WeatherObservation


class WeatherClient(ABC):
    mapper: ObservationMapper

    @abstractmethod
    def fetch_raw_observation(self, location: str):
        """Fetch the raw JSON from whatever API."""
        ...

    def get_current_weather(self, location: str) -> WeatherObservation:
        points, forecast, observations = self.fetch_raw_observation(location)
        return self.mapper.map(points, forecast, observations)


# optional: a factory to pick your client by name
def get_weather_client(source: str = "noaa") -> WeatherClient:
    if source == "noaa":
        from .noaa_client import NOAAWeatherClient

        return NOAAWeatherClient()
    elif source == "wttr":
        from .wttr_client import WTTRWeatherClient

        return WTTRWeatherClient()
    else:
        raise ValueError(f"Unknown source {source!r}")
