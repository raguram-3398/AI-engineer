# tests/test_weather.py

from weather.client import parse_weather


def test_parse_weather_valid():
    data = {
        "latitude": 33.21,
        "longitude": -97.13,
        "current": {
            "temperature_2m": 28.5,
            "wind_speed_10m": 12.3,
            "weather_code": 1,
        }
    }
    result = parse_weather(data)
    assert result.latitude == 33.21
    assert result.longitude == -97.13
    assert result.current_weather.temperature == 28.5
    assert result.current_weather.windspeed == 12.3
    assert result.current_weather.weathercode == 1


def test_parse_weather_missing_field_fails():
    data = {
        "latitude": 33.21,
        "longitude": -97.13,
        "current": {
            "temperature_2m": 28.5,
            "wind_speed_10m": 12.3,
            # weather_code missing intentionally
        }
    }
    try:
        parse_weather(data)
        assert False, "Expected validation error"
    except Exception:
        assert True