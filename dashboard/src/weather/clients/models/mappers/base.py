from abc import ABC, abstractmethod
from typing import Any, Dict

from dashboard.src.weather.clients.models.observation import WeatherObservation


class ObservationMapper(ABC):
    @abstractmethod
    def map(
        self,
        points: Dict[str, Any],
        forecast: Dict[str, Any],
        observations: Dict[str, Any],
    ) -> WeatherObservation:
        """Turn raw JSON into an Observation."""
        ...
