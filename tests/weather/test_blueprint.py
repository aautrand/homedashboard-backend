import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from dashboard.src.weather import weather


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["LAT_LONG"] = "40.7,-74.0"
    app.config["OPEN_WEATHER_API_KEY"] = "test-key"
    return app


@pytest.fixture
def client(app):
    app.register_blueprint(weather)
    return app.test_client()


class TestCurrentEndpoint:

    @patch("dashboard.src.weather.get_weather_client")
    def test_success(self, mock_factory, client):
        mock_client = MagicMock()
        mock_client.fetch_raw_observation.return_value = {"condition": "Clear +20C"}
        mock_factory.return_value = mock_client

        resp = client.get("/weather/current")
        assert resp.status_code == 200
        mock_factory.assert_called_once_with("wttr")


class TestOpenWeatherEndpoint:

    @patch("dashboard.src.weather.OpenWeather")
    @patch("dashboard.src.weather.get_weather_client")
    def test_success(self, mock_factory, mock_ow_cls, client):
        mock_client = MagicMock()
        mock_client.get_current_weather.return_value = {"temp": 20}
        mock_client.get_forecast_weather.return_value = {"list": []}
        mock_factory.return_value = mock_client

        mock_combined = MagicMock()
        mock_combined.to_json.return_value = json.dumps({"name": "NY"})
        mock_ow_cls.from_current_and_forecast.return_value = mock_combined

        resp = client.get("/weather/open-weather")
        assert resp.status_code == 200
        mock_factory.assert_called_once_with("open-weather")
