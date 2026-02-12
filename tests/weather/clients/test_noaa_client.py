from unittest.mock import MagicMock, patch

from dashboard.src.weather.clients.noaa_client import NOAAWeatherClient


class TestNOAAWeatherClient:

    @patch("dashboard.src.weather.clients.noaa_client.requests")
    def test_fetch_raw_observation(self, mock_requests):
        mock_points_resp = MagicMock()
        mock_points_resp.json.return_value = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/OKX/33,37/forecast",
                "radarStation": "KOKX",
            }
        }

        mock_forecast_resp = MagicMock()
        mock_forecast_resp.json.return_value = {"properties": {"periods": []}}

        mock_obs_resp = MagicMock()
        mock_obs_resp.json.return_value = {
            "properties": {"temperature": {"value": 20}}
        }

        mock_requests.get.side_effect = [
            mock_points_resp,
            mock_forecast_resp,
            mock_obs_resp,
        ]

        client = NOAAWeatherClient()
        pts, forecast, observations = client.fetch_raw_observation("40.7,-74.0")

        assert mock_requests.get.call_count == 3
        assert pts["properties"]["radarStation"] == "KOKX"

    def test_has_mapper(self):
        client = NOAAWeatherClient()
        assert client.mapper is not None
