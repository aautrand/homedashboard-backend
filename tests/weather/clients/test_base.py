from unittest.mock import patch

import pytest

from dashboard.src.weather.clients.base import get_weather_client


class TestGetWeatherClient:

    def test_unknown_source_raises(self):
        with pytest.raises(ValueError, match="Unknown source"):
            get_weather_client("unknown")

    @patch("dashboard.src.weather.clients.noaa_client.requests")
    def test_noaa_source(self, mock_req):
        client = get_weather_client("noaa")
        from dashboard.src.weather.clients.noaa_client import NOAAWeatherClient

        assert isinstance(client, NOAAWeatherClient)

    @patch("dashboard.src.weather.clients.wttr_client.requests")
    def test_wttr_source(self, mock_req):
        client = get_weather_client("wttr")
        from dashboard.src.weather.clients.wttr_client import WTTRWeatherClient

        assert isinstance(client, WTTRWeatherClient)

    def test_open_weather_source(self):
        from flask import Flask

        app = Flask(__name__)
        app.config["OPEN_WEATHER_API_KEY"] = "test-key"
        with app.app_context():
            client = get_weather_client("open-weather")
            assert client is not None
