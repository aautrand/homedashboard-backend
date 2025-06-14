from typing import Any, Dict, Optional

from dashboard.src.utils.helpers import _get
from dashboard.src.weather.clients.models.observation import Observation

from .base import ObservationMapper



class NOAAObservationMapper(ObservationMapper):
    def map(self, raw: Dict[str, Any]) -> Observation:
        props = raw.get("properties", {})
        station_url = props.get("station") or raw.get("id", "")
        station_id = station_url.rstrip("/").split("/")[-1] or None
        raw_message = props.get("rawMessage")

        return Observation(
            station_id=station_id,
            wind_speed=_get(props, "windSpeed"),
            wind_direction=_get(props, "windDirection"),
            temperature=_get(props, "temperature"),
            dewpoint=_get(props, "dewpoint"),
            visibility=_get(props, "visibility"),
            raw_message=raw_message,
        )
