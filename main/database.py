"""
Weather Data Retrieval System
=============================
A comprehensive system for retrieving and processing weather data using 
the MET Norway API with geolocation capabilities.

This module provides two main classes:
1. Location: For converting location names to geographical coordinates
2. Weather: For fetching and processing weather data including feels-like temperature calculations
"""

from datetime import datetime
from geopy.geocoders import Nominatim
import requests
import time as t


class Location:
    """
    Location data retrieval class that fetches geographical coordinates using geopy.

    This class provides functionality to convert location names (city, country)
    into geographical coordinates (latitude, longitude) using the Nominatim geocoder.
    """
    geolocator = Nominatim(user_agent="pape")

    def __init__(self, country_code, city_code):
        """
        Initialize Location object with location parameters.

        Args:
            country_code (str): ISO country code (e.g., "IN", "US")
            city_code (str): City name or postal code (e.g., "Delhi", "232101")
        """
        self.city_code = city_code
        self.country_code = country_code

    def get_coordinates(self):
        """
        Convert location name to geographical coordinates (latitude and longitude).

        Returns:
            tuple: (latitude, longitude) if successful, (None, None) on failure
        """
        try:
            location = self.geolocator.geocode(f"{self.city_code}, {self.country_code}")
            if location:
                return location.latitude, location.longitude
            else:
                print("Location not found.")
                return None, None
        except Exception as e:
            print(f"Error retrieving coordinates: {e}")
            return None, None


class Weather:
    """
    Weather data retrieval and processing class that fetches data from MET Norway API.

    This class provides comprehensive weather data including:
    - Current temperature, humidity, and wind speed
    - Weather conditions with human-readable descriptions
    - Feels-like temperature (heat index for hot, wind chill for cold)
    - Next 24-hour temperature forecasts
    - Next 10 days of weather data (min/max temp, symbols, precipitation)

    The class implements retry logic for API calls and caches the fetched data
    to avoid redundant requests.
    """

    # HTTP headers for API requests with proper user agent identification
    headers = {
        'User-Agent': 'pape_weather_website/1.0 (papwhv@outlook.com)'
    }

    # Comprehensive mapping of MET Norway weather symbol codes to human-readable descriptions
    WEATHER_CONDITIONS = {
        "clearsky_day": "Clear sky (Sunny)",
        "clearsky_night": "Clear sky",
        "partlycloudy_day": "Partly cloudy",
        "partlycloudy_night": "Partly cloudy",
        "cloudy": "Cloudy",
        "lightrainshowers_day": "Light rain showers",
        "rainshowers_day": "Rain showers",
        "heavyrainshowers_day": "Heavy rain showers",
        "lightrain": "Light rain",
        "rain": "Rain",
        "heavyrain": "Heavy rain",
        "lightssnowshowers_day": "Light snow showers",
        "snowshowers_day": "Snow showers",
        "heavysnowshowers_day": "Heavy snow showers",
        "lightsnow": "Light snow",
        "snow": "Snow",
        "heavysnow": "Heavy snow",
        "fog": "Foggy",
        "sleet": "Sleet",
        "lightsleet": "Light sleet",
        "heavysleet": "Heavy sleet",
        "sleetshowers_day": "Sleet showers",
        "lightssleetshowers_day": "Light sleet showers",
        "heavysleetshowers_day": "Heavy sleet showers",
        "thunderstorms": "Thunderstorms",
        "lightrainshowersandthunder_day": "Light rain showers and thunder",
        "rainandthunder": "Rain and thunder",
        "heavyrainandthunder": "Heavy rain and thunder",
        "fair_day": "Fair (Sunny)",
    }

    def __init__(self, country_code, city_code):
        """
        Initialize Weather object with location parameters.

        Args:
            country_code (str): ISO country code (e.g., "IN", "US")
            city_code (str): City name or postal code (e.g., "Delhi", "232101")
        """
        self.city_code = city_code
        self.country_code = country_code
        self._cached_data = None  # Will store (air_temp, humidity, wind, desc, symbol, temp_24h, weekly)

    def __str__(self):
        return self.country_code

    def weather_json(self):
        """
        Fetch raw weather data from MET Norway API with retry logic.

        Returns:
            dict: JSON response from API, or None on failure
        """
        max_retries = 50
        attempts = 0

        while attempts < max_retries:
            try:
                # Get coordinates using geopy (reuse Location class if desired)
                geolocator = Nominatim(user_agent="pape")
                location = geolocator.geocode(f"{self.city_code}, {self.country_code}")
                if not location:
                    print("Location not found.")
                    return None
                latitude, longitude = location.latitude, location.longitude

                url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={latitude}&lon={longitude}"
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()

            except Exception as e:
                attempts += 1
                print(f"Attempt {attempts} to retrieve weather data failed: {e}")
                t.sleep(5)  # Wait before retrying

        print("Max retries reached. Could not fetch weather data.")
        return None

    def weather_data(self):
        """
        Extract and process specific weather parameters from API response.
        Caches the result so subsequent calls return instantly.

        Returns:
            tuple: (air_temperature, relative_humidity, wind_speed,
                    weather_description, symbol_code,
                    temp_24h_list, weekly_data_dict)
        """
        if self._cached_data is not None:
            return self._cached_data

        json = self.weather_json()
        if json is None:
            return (None, None, None, None, None, None, None)

        timeseries = json['properties']['timeseries']
        if not timeseries:
            print("No forecast data available.")
            return (None, None, None, None, None, None, None)

        # --- Current hour data ---
        current = timeseries[0]['data']['instant']['details']
        air_temperature = current['air_temperature']
        relative_humidity = current['relative_humidity']
        wind_speed = current['wind_speed']

        # --- Weather symbol & description (next 1 hour) ---
        next_1 = timeseries[0]['data'].get('next_1_hours', {})
        symbol_code = next_1.get('summary', {}).get('symbol_code')
        weather_description = self.WEATHER_CONDITIONS.get(symbol_code, "Unknown")

        # --- 24-hour temperature forecast (first 24 entries) ---
        temp_24h = []
        for i in range(min(24, len(timeseries))):
            temp_24h.append(timeseries[i]['data']['instant']['details']['air_temperature'])

        # --- Weekly data (group by date) ---
        weekly_data = {}

        for entry in timeseries:
            time_str = entry["time"]
            date_key = time_str

            instant = entry["data"]["instant"]["details"]
            current_temp = instant.get("air_temperature")
            wind_sp = instant.get("wind_speed")
            pressure = instant.get("air_pressure_at_sea_level")

            if 'next_1_hours' in entry['data']:
                next_1 = entry["data"].get("next_1_hours", {})
                precip = next_1.get("details", {}).get("precipitation_amount")
                symbol = next_1.get("summary", {}).get("symbol_code")

            elif 'next_6_hours' in entry['data']:
                next_6 = entry["data"].get("next_6_hours", {})
                symbol = next_6.get("summary", {}).get("symbol_code")
                precip = next_6.get("details", {}).get("precipitation_amount")

            record = {
                "time": time_str,
                "temp": current_temp,
                "wind_speed": wind_sp,
                "pressure": pressure,
                "precip": precip,
                "symbol": symbol,
            }

            # Initialize the date entry if it doesn't exist
            if date_key not in weekly_data:
                weekly_data[date_key] = {
                    "entries": [],
                    "min_temp": None,
                    "max_temp": None
                }

            weekly_data[date_key[:]]["entries"].append(record)

            # Update min/max for the day
            if current_temp is not None:
                if (weekly_data[date_key]["min_temp"] is None or
                        current_temp < weekly_data[date_key]["min_temp"]):
                    weekly_data[date_key]["min_temp"] = current_temp
                if (weekly_data[date_key]["max_temp"] is None or
                        current_temp > weekly_data[date_key]["max_temp"]):
                    weekly_data[date_key]["max_temp"] = current_temp
            weekly = {}
            a = list(weekly_data.keys())
            for i ,_ in enumerate(weekly_data): 
                 if a[i][:10] in weekly:
                    continue
                 else:
                    weekly[a[i][:10]] = weekly_data[a[i]]

        self._cached_data = (air_temperature ,relative_humidity ,wind_speed ,weather_description ,symbol_code ,temp_24h, weekly)
        return self._cached_data

    def feels_like_temperature(self):
        """
        Calculate feels-like temperature based on environmental conditions.

        Uses appropriate formulas based on temperature:
        - Heat Index formula (when temp ≥ 27°C): Considers humidity effect
        - Wind Chill formula (when temp ≤ 10°C): Considers wind cooling effect
        - Actual temperature (moderate conditions): No adjustment needed

        The formulas are originally in Fahrenheit and converted back to Celsius.

        Returns:
            float: Feels-like temperature in °C (rounded to 2 decimal places)
                  or None if required data is missing.
        """
        data = self.weather_data()
        temperature, humidity, wind_speed, *_ = data
        if temperature is None:
            return None

        # Convert Celsius to Fahrenheit for formulas
        temp_f = (temperature * 9 / 5) + 32

        # Apply Heat Index formula for hot conditions
        if temperature >= 27 and humidity is not None:
            hi_f = (
                -42.379 + 2.04901523 * temp_f + 10.14333127 * humidity
                - 0.22475541 * temp_f * humidity
                - 0.00683783 * temp_f ** 2
                - 0.05481717 * humidity ** 2
                + 0.00122874 * temp_f ** 2 * humidity
                + 0.00085282 * temp_f * humidity ** 2
                - 0.00000199 * temp_f ** 2 * humidity ** 2
            )
            feels_like_c = (hi_f - 32) * 5 / 9
            return round(feels_like_c, 2)

        # Apply Wind Chill formula for cold conditions
        elif temperature <= 10 and wind_speed is not None:
            wc_f = (
                35.74 + 0.6215 * temp_f
                - 35.75 * (wind_speed ** 0.16)
                + 0.4275 * temp_f * (wind_speed ** 0.16)
            )
            feels_like_c = (wc_f - 32) * 5 / 9
            return round(feels_like_c, 2)

        # Return actual temperature for moderate conditions
        return round(temperature, 2)


if __name__ == "__main__":
    # Example usage with a location in India (Mumbai postal code)
    weather = Weather(country_code="IN", city_code="400001")
    air_temp, humidity, wind, desc, symbol, temp_24h, weekly = weather.weather_data()
    feels_like = weather.feels_like_temperature()

    if air_temp is not None:
        print(f"Location: Mumbai, India")
        print(f"Current conditions: {desc}")
        print(f"Temperature: {air_temp}°C")
        print(f"Feels like: {feels_like}°C")
        print(f"Humidity: {int(humidity)}%")
        print(f"Wind speed: {wind} m/s")
        print("\n--- 24-hour temperature forecast ---")
        print([round(t, 1) for t in temp_24h])
        print(weekly)

    