from abc import ABC, abstractmethod
from typing import Any, Dict

from dashboard.src.weather.clients.models.observation import Observation


class ObservationMapper(ABC):
    @abstractmethod
    def map(self, raw: Dict[str, Any]) -> Observation:
        """Turn raw JSON into an Observation."""
        ...
