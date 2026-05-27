from weather.client import WeatherResponse, get_weather


def get_coordinates() -> tuple[float, float]:
    """Prompt the user to input geographic coordinates via the command line."""
    lat = float(input("Enter the Latitude: "))
    lon = float(input("Enter the Longitude: "))
    return lat, lon


def display_weather(weather: WeatherResponse) -> None:
    """Display formatted weather information to the user."""
    print("   ---   Current Weather   ---")
    print(f"Temperature: {weather.current_weather.temperature}°c")
    print(f"Topspeed: {weather.current_weather.windspeed}km/h")
    print(f"Weather Code: {weather.current_weather.weathercode}")


def main() -> None:
    """Runs the weather CLI application."""
    try:
        lat, lon = get_coordinates()
        weather = get_weather(lat, lon)
        display_weather(weather)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()