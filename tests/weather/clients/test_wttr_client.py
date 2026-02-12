from unittest.mock import MagicMock, patch

from dashboard.src.weather.clients.wttr_client import WTTRWeatherClient


class TestWTTRWeatherClient:

    @patch("dashboard.src.weather.clients.wttr_client.requests")
    def test_fetch_raw_observation(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.text = "Clear +20°C 10km/h"
        mock_requests.get.return_value = mock_resp

        client = WTTRWeatherClient()
        result = client.fetch_raw_observation("40.7,-74.0")

        assert result == {"condition": "Clear +20°C 10km/h"}
        mock_requests.get.assert_called_once_with(
            "http://wttr.in/40.7,-74.0?format=%C+%t+%W"
        )
