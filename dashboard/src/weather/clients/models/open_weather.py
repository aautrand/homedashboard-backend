import json
from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass
class Coord:
    lon: float
    lat: float


@dataclass
class Weather:
    id: int
    main: str
    description: str
    icon: str


@dataclass
class Main:
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int
    sea_level: Optional[int] = None
    grnd_level: Optional[int] = None
    temp_kf: Optional[float] = None


@dataclass
class Wind:
    speed: float
    deg: int
    gust: Optional[float] = None


@dataclass
class Clouds:
    all: int


@dataclass
class Rain:
    one_hour: Optional[float] = None
    three_hours: Optional[float] = None


@dataclass
class Sys:
    type: Optional[int] = None
    id: Optional[int] = None
    country: Optional[str] = None
    sunrise: Optional[int] = None
    sunset: Optional[int] = None
    pod: Optional[str] = None


@dataclass
class ForecastEntry:
    dt: int
    main: Main
    weather: List[Weather]
    clouds: Clouds
    wind: Wind
    sys: Sys
    visibility: int
    pop: Optional[float] = None
    rain: Optional[Rain] = None
    dt_txt: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ForecastEntry":
        main = Main(**data["main"])
        weather = [Weather(**w) for w in data.get("weather", [])]
        clouds = Clouds(**data["clouds"])
        wind = Wind(**data["wind"])
        visibility = data.get("visibility", 0)
        pop = data.get("pop")
        rain_info = data.get("rain", {})
        rain = None
        if rain_info:
            rain = Rain(three_hours=rain_info.get("3h"))
        sys = Sys(pod=data.get("sys", {}).get("pod"))
        return cls(
            dt=data["dt"],
            main=main,
            weather=weather,
            clouds=clouds,
            wind=wind,
            visibility=visibility,
            pop=pop,
            rain=rain,
            sys=sys,
            dt_txt=data.get("dt_txt"),
        )


@dataclass
class City:
    id: int
    name: str
    coord: Coord
    country: str
    population: int
    timezone: int
    sunrise: int
    sunset: int

    @classmethod
    def from_dict(cls, data: dict) -> "City":
        coord = Coord(**data["coord"])
        return cls(
            id=data["id"],
            name=data["name"],
            coord=coord,
            country=data["country"],
            population=data["population"],
            timezone=data["timezone"],
            sunrise=data["sunrise"],
            sunset=data["sunset"],
        )


@dataclass
class OpenWeather:
    # Current weather
    coord: Coord
    weather: List[Weather]
    base: str
    main: Main
    visibility: int
    wind: Wind
    rain: Optional[Rain]
    clouds: Clouds
    dt: int
    sys: Sys
    timezone: int
    id: int
    name: str
    cod: int
    # Forecast
    message: int
    cnt: int
    forecast: List[ForecastEntry]
    city: City

    @classmethod
    def from_current_and_forecast(cls, current: dict, forecast: dict) -> "OpenWeather":
        # Current weather
        coord = Coord(**current["coord"])
        weather = [Weather(**w) for w in current.get("weather", [])]
        main = Main(**current["main"])
        visibility = current.get("visibility", 0)
        wind = Wind(**current["wind"])
        rain_info = current.get("rain", {})
        rain = None
        if rain_info:
            rain = Rain(one_hour=rain_info.get("1h"))
        clouds = Clouds(**current["clouds"])
        sys_data = current.get("sys", {})
        sys = Sys(
            type=sys_data.get("type"),
            id=sys_data.get("id"),
            country=sys_data.get("country"),
            sunrise=sys_data.get("sunrise"),
            sunset=sys_data.get("sunset"),
        )

        # Forecast
        message = forecast.get("message", 0)
        cnt = forecast.get("cnt", 0)
        forecast_list = [
            ForecastEntry.from_dict(item) for item in forecast.get("list", [])
        ]
        city = City.from_dict(forecast.get("city", {}))
        return cls(
            coord=coord,
            weather=weather,
            base=current.get("base", ""),
            main=main,
            visibility=visibility,
            wind=wind,
            rain=rain,
            clouds=clouds,
            dt=current.get("dt", 0),
            sys=sys,
            timezone=current.get("timezone", 0),
            id=current.get("id", 0),
            name=current.get("name", ""),
            cod=int(current.get("cod", 0)),
            message=message,
            cnt=cnt,
            forecast=forecast_list,
            city=city,
        )

    @property
    def daily_min_temp(self) -> float:
        """Minimum temperature across current and forecast entries."""
        temps = [self.main.temp_min] + [entry.main.temp_min for entry in self.forecast]
        return min(temps)

    @property
    def daily_max_temp(self) -> float:
        """Maximum temperature across current and forecast entries."""
        temps = [self.main.temp_max] + [entry.main.temp_max for entry in self.forecast]
        return max(temps)

    @property
    def icons(self) -> List[str]:
        """Maximum temperature across current and forecast entries."""
        icons = [
            f"https://openweathermap.org/img/wn/{entry.icon}@2x.png"
            for entry in self.weather
        ]
        return icons

    def to_json(self) -> str:
        """
        Serialize the CombinedWeatherData instance to a JSON string.
        """
        # Convert dataclass hierarchy to nested dict
        data_dict = asdict(self)
        # Include computed properties
        data_dict["daily_min_temp"] = self.daily_min_temp
        data_dict["daily_max_temp"] = self.daily_max_temp
        data_dict["icons"] = self.icons
        return json.dumps(data_dict)
