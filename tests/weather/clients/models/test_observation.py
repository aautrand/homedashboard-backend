import json

from dashboard.src.weather.clients.models.observation import WeatherObservation


class TestWeatherObservation:

    def _make_observation(self, **kwargs):
        defaults = {
            "text_description": "Partly Cloudy",
            "station_id": "KOKX",
            "wind_speed": 10.5,
            "wind_direction": 180.0,
            "temperature": 22.0,
            "temperature_f": 71.6,
            "dewpoint": 15.0,
            "visibility": 16000.0,
            "raw_message": "KOKX 221856Z 18010KT",
        }
        defaults.update(kwargs)
        return WeatherObservation(**defaults)

    def test_create(self):
        obs = self._make_observation()
        assert obs.text_description == "Partly Cloudy"
        assert obs.station_id == "KOKX"
        assert obs.temperature == 22.0

    def test_to_dict(self):
        obs = self._make_observation()
        d = obs.to_dict()
        assert isinstance(d, dict)
        assert d["text_description"] == "Partly Cloudy"
        assert d["temperature"] == 22.0

    def test_to_json(self):
        obs = self._make_observation()
        j = obs.to_json()
        parsed = json.loads(j)
        assert parsed["station_id"] == "KOKX"

    def test_optional_fields(self):
        obs = WeatherObservation(
            text_description=None,
            station_id=None,
            wind_speed=None,
            wind_direction=None,
            temperature=None,
            temperature_f=None,
            dewpoint=None,
            visibility=None,
            raw_message=None,
        )
        d = obs.to_dict()
        assert all(v is None for v in d.values())
