from unittest.mock import MagicMock, patch

from dashboard.src.weather.weather_service import WeatherService


class TestWeatherService:
    @patch("dashboard.src.weather.weather_service.OpenWeather")
    def test_combines_current_and_forecast(self, mock_open_weather):
        client = MagicMock()
        client.get_current_weather.return_value = {"current": 1}
        client.get_forecast_weather.return_value = {"forecast": 1}

        result = WeatherService(client, "1,2").get_weather()

        client.get_current_weather.assert_called_once_with("1,2")
        client.get_forecast_weather.assert_called_once_with("1,2")
        mock_open_weather.from_current_and_forecast.assert_called_once_with(
            {"current": 1}, {"forecast": 1}
        )
        assert result is mock_open_weather.from_current_and_forecast.return_value
