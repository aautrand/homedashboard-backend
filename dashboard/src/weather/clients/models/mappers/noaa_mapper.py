from typing import Any, Dict, Optional

from dashboard.src.utils.helpers import _get
from dashboard.src.weather.clients.models.observation import WeatherObservation

from .base import ObservationMapper


class NOAAObservationMapper(ObservationMapper):
    def map(
        self,
        points: Dict[str, Any],
        forecast: Dict[str, Any],
        observations: Dict[str, Any],
    ) -> WeatherObservation:
        points_props = observations.get("properties", {})
        forecast_props = observations.get("properties", {})
        observation_props = observations.get("properties", {})
        station_url = observation_props.get("station") or observations.get("id", "")
        station_id = station_url.rstrip("/").split("/")[-1] or None
        raw_message = observation_props.get("rawMessage")

        return WeatherObservation(
            text_description=_get(observation_props, "textDescription"),
            station_id=station_id,
            wind_speed=_get(observation_props, "windSpeed"),
            wind_direction=_get(observation_props, "windDirection"),
            temperature=_get(observation_props, "temperature"),
            temperature_f=(_get(observation_props, "temperature") * 1.8) + 32,
            dewpoint=_get(observation_props, "dewpoint"),
            visibility=_get(observation_props, "visibility"),
            raw_message=raw_message,
        )
