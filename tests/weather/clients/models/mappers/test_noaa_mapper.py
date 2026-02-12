from dashboard.src.weather.clients.models.mappers.noaa_mapper import NOAAObservationMapper
from dashboard.src.weather.clients.models.observation import WeatherObservation


class TestNOAAObservationMapper:

    def _make_observations(self, temp_value=20.0):
        return {
            "id": "https://api.weather.gov/stations/KOKX/observations/latest",
            "properties": {
                "station": "https://api.weather.gov/stations/KOKX",
                "textDescription": {"value": "Partly Cloudy"},
                "windSpeed": {"value": 10.0},
                "windDirection": {"value": 180.0},
                "temperature": {"value": temp_value},
                "dewpoint": {"value": 15.0},
                "visibility": {"value": 16000.0},
                "rawMessage": "KOKX 221856Z",
            },
        }

    def test_map_basic(self):
        mapper = NOAAObservationMapper()
        observations = self._make_observations()

        result = mapper.map(
            points={},
            forecast={},
            observations=observations,
        )

        assert isinstance(result, WeatherObservation)
        assert result.station_id == "KOKX"
        assert result.temperature == 20.0
        assert result.wind_speed == 10.0
        assert result.raw_message == "KOKX 221856Z"

    def test_temperature_f_conversion(self):
        mapper = NOAAObservationMapper()
        observations = self._make_observations(temp_value=0.0)
        result = mapper.map({}, {}, observations)
        assert result.temperature_f == 32.0

    def test_station_id_from_url(self):
        mapper = NOAAObservationMapper()
        observations = self._make_observations()
        result = mapper.map({}, {}, observations)
        assert result.station_id == "KOKX"

    def test_station_id_from_id_fallback(self):
        mapper = NOAAObservationMapper()
        observations = self._make_observations()
        observations["properties"]["station"] = None
        result = mapper.map({}, {}, observations)
        # Falls back to observations["id"] URL
        assert result.station_id == "latest"
