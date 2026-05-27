import requests
from pydantic import BaseModel
from typing import Dict, Any

class CurrentWeather(BaseModel):
    temperature: float
    windspeed: float
    weathercode: int


class WeatherResponse(BaseModel):
    latitude: float
    longitude: float
    current_weather: CurrentWeather


def parse_weather(data: Dict[str, Any]) -> WeatherResponse:
    """Convert raw Open-Meteo API response into a validated WeatherResponse model."""
    return WeatherResponse(
        latitude=data["latitude"],
        longitude=data["longitude"],
        current_weather=CurrentWeather(
            temperature=data["current"]["temperature_2m"],
            windspeed=data["current"]["wind_speed_10m"],
            weathercode=data["current"]["weather_code"],
        ),
    )


def get_weather(latitude: float, longitude: float) -> WeatherResponse:
    """Fetch current weather data from the Open-Meteo API for a given location."""
    url = "https://api.open-meteo.com/v1/forecast"
    params: Dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m,weather_code",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            data = data[-1]
        return parse_weather(data)
    except requests.exceptions.Timeout:
        raise RuntimeError("Weather API timed out") from None

    except requests.exceptions.ConnectionError:
        raise RuntimeError("No network connection") from None

    except requests.exceptions.HTTPError:
        raise RuntimeError(f"Bad response: {response.status_code}") from None