from abc import ABC


class WeatherClient(ABC): ...


# optional: a factory to pick your client by name
def get_weather_client(source: str = "noaa"):
    if source == "noaa":
        from .noaa_client import NOAAWeatherClient

        return NOAAWeatherClient()
    elif source == "wttr":
        from .wttr_client import WTTRWeatherClient

        return WTTRWeatherClient()
    elif source == "open-weather":
        from .open_weather_client import OpenWeatherClient

        return OpenWeatherClient()
    else:
        raise ValueError(f"Unknown source {source!r}")
