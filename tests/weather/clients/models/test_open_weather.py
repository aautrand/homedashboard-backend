import json

from dashboard.src.weather.clients.models.open_weather import (
    City,
    Coord,
    ForecastEntry,
    Main,
    OpenWeather,
    Rain,
    Weather,
)


def _make_current_data(**overrides):
    data = {
        "coord": {"lon": -74.0, "lat": 40.7},
        "weather": [
            {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}
        ],
        "base": "stations",
        "main": {
            "temp": 20.0,
            "feels_like": 19.0,
            "temp_min": 18.0,
            "temp_max": 22.0,
            "pressure": 1013,
            "humidity": 60,
        },
        "visibility": 10000,
        "wind": {"speed": 5.0, "deg": 180},
        "clouds": {"all": 0},
        "dt": 1700000000,
        "sys": {
            "type": 1,
            "id": 1234,
            "country": "US",
            "sunrise": 1699990000,
            "sunset": 1700030000,
        },
        "timezone": -18000,
        "id": 5128581,
        "name": "New York",
        "cod": 200,
    }
    data.update(overrides)
    return data


def _make_forecast_data(**overrides):
    data = {
        "cod": "200",
        "message": 0,
        "cnt": 1,
        "list": [
            {
                "dt": 1700010000,
                "main": {
                    "temp": 19.0,
                    "feels_like": 18.0,
                    "temp_min": 17.0,
                    "temp_max": 21.0,
                    "pressure": 1012,
                    "humidity": 65,
                },
                "weather": [
                    {
                        "id": 801,
                        "main": "Clouds",
                        "description": "few clouds",
                        "icon": "02d",
                    }
                ],
                "clouds": {"all": 20},
                "wind": {"speed": 4.0, "deg": 200},
                "visibility": 10000,
                "pop": 0.1,
                "sys": {"pod": "d"},
                "dt_txt": "2025-11-15 12:00:00",
            }
        ],
        "city": {
            "id": 5128581,
            "name": "New York",
            "coord": {"lat": 40.7, "lon": -74.0},
            "country": "US",
            "population": 8175133,
            "timezone": -18000,
            "sunrise": 1699990000,
            "sunset": 1700030000,
        },
    }
    data.update(overrides)
    return data


class TestCoord:

    def test_create(self):
        c = Coord(lon=-74.0, lat=40.7)
        assert c.lon == -74.0
        assert c.lat == 40.7


class TestWeather:

    def test_create(self):
        w = Weather(id=800, main="Clear", description="clear sky", icon="01d")
        assert w.description == "clear sky"


class TestMain:

    def test_create(self):
        m = Main(
            temp=20.0,
            feels_like=19.0,
            temp_min=18.0,
            temp_max=22.0,
            pressure=1013,
            humidity=60,
        )
        assert m.temp == 20.0

    def test_optional_fields(self):
        m = Main(
            temp=20.0,
            feels_like=19.0,
            temp_min=18.0,
            temp_max=22.0,
            pressure=1013,
            humidity=60,
            sea_level=1013,
            grnd_level=1010,
            temp_kf=0.5,
        )
        assert m.sea_level == 1013


class TestRain:

    def test_create(self):
        r = Rain(one_hour=1.5, three_hours=3.0)
        assert r.one_hour == 1.5

    def test_defaults(self):
        r = Rain()
        assert r.one_hour is None
        assert r.three_hours is None


class TestForecastEntry:

    def test_from_dict(self):
        data = _make_forecast_data()["list"][0]
        entry = ForecastEntry.from_dict(data)
        assert entry.main.temp == 19.0
        assert len(entry.weather) == 1
        assert entry.weather[0].description == "few clouds"
        assert entry.wind.speed == 4.0
        assert entry.dt_txt == "2025-11-15 12:00:00"

    def test_from_dict_with_rain(self):
        data = _make_forecast_data()["list"][0]
        data["rain"] = {"3h": 2.5}
        entry = ForecastEntry.from_dict(data)
        assert entry.rain is not None
        assert entry.rain.three_hours == 2.5

    def test_from_dict_without_rain(self):
        data = _make_forecast_data()["list"][0]
        entry = ForecastEntry.from_dict(data)
        assert entry.rain is None


class TestCity:

    def test_from_dict(self):
        data = _make_forecast_data()["city"]
        city = City.from_dict(data)
        assert city.name == "New York"
        assert city.coord.lat == 40.7
        assert city.country == "US"


class TestOpenWeather:

    def test_from_current_and_forecast(self):
        current = _make_current_data()
        forecast = _make_forecast_data()

        ow = OpenWeather.from_current_and_forecast(current, forecast)
        assert ow.name == "New York"
        assert ow.main.temp == 20.0
        assert len(ow.weather) == 1
        assert ow.weather[0].description == "clear sky"
        assert len(ow.forecast) == 1
        assert ow.city.name == "New York"

    def test_daily_min_temp(self):
        current = _make_current_data()
        forecast = _make_forecast_data()

        ow = OpenWeather.from_current_and_forecast(current, forecast)
        # current temp_min=18, forecast temp_min=17
        assert ow.daily_min_temp == 17.0

    def test_daily_max_temp(self):
        current = _make_current_data()
        forecast = _make_forecast_data()

        ow = OpenWeather.from_current_and_forecast(current, forecast)
        # current temp_max=22, forecast temp_max=21
        assert ow.daily_max_temp == 22.0

    def test_icons(self):
        current = _make_current_data()
        forecast = _make_forecast_data()

        ow = OpenWeather.from_current_and_forecast(current, forecast)
        assert ow.icons == ["https://openweathermap.org/img/wn/01d@2x.png"]

    def test_to_json(self):
        current = _make_current_data()
        forecast = _make_forecast_data()

        ow = OpenWeather.from_current_and_forecast(current, forecast)
        j = ow.to_json()
        parsed = json.loads(j)
        assert parsed["name"] == "New York"
        assert "daily_min_temp" in parsed
        assert "daily_max_temp" in parsed
        assert "icons" in parsed

    def test_with_rain(self):
        current = _make_current_data(rain={"1h": 0.5})
        forecast = _make_forecast_data()

        ow = OpenWeather.from_current_and_forecast(current, forecast)
        assert ow.rain is not None
        assert ow.rain.one_hour == 0.5

    def test_without_rain(self):
        current = _make_current_data()
        forecast = _make_forecast_data()

        ow = OpenWeather.from_current_and_forecast(current, forecast)
        assert ow.rain is None

    def test_multiple_forecast_entries(self):
        current = _make_current_data()
        forecast = _make_forecast_data()
        # Add another forecast entry with extreme temps
        forecast["list"].append(
            {
                "dt": 1700020000,
                "main": {
                    "temp": 25.0,
                    "feels_like": 24.0,
                    "temp_min": 10.0,
                    "temp_max": 30.0,
                    "pressure": 1010,
                    "humidity": 70,
                },
                "weather": [
                    {
                        "id": 500,
                        "main": "Rain",
                        "description": "light rain",
                        "icon": "10d",
                    }
                ],
                "clouds": {"all": 80},
                "wind": {"speed": 8.0, "deg": 270},
                "visibility": 8000,
                "sys": {"pod": "d"},
            }
        )

        ow = OpenWeather.from_current_and_forecast(current, forecast)
        assert ow.daily_min_temp == 10.0
        assert ow.daily_max_temp == 30.0
