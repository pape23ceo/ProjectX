from datetime import datetime
from geopy.geocoders import Nominatim
import requests
import time as t
from django.core.cache import cache

class Weather:
    headers = {
        'User-Agent': 'pape_weather_website/1.0 (papwhv@outlook.com)'
    }

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
        self.city_code = city_code
        self.country_code = country_code
        # Internal placeholders so we don't calculate weather calculations twice per instance lifespan
        self._processed_data = None 

    def __str__(self):
        return self.country_code

    def get_coordinates(self):
        """
        Retrieves coordinates with an independent long-term cache (30 days).
        """
        geo_cache_key = f"geo_{self.country_code}_{self.city_code}"
        coords = cache.get(geo_cache_key)
        
        if coords is not None:
            return coords

        try:
            geolocator = Nominatim(user_agent="pape_weather_website")
            location = geolocator.geocode(f"{self.city_code}, {self.country_code}")
            if location:
                coords = (location.latitude, location.longitude)
                # Cache coordinates for 1 hour (3600 seconds)
                cache.set(geo_cache_key, coords, timeout=3600)
                return coords
        except Exception as e:
            print(f"Geocoding failed: {e}")
        
        return None

    def weather_json(self):
        """
        Fetch raw weather data using cached coordinates and retry logic.
        """
        coordinates = self.get_coordinates()
        if not coordinates:
            print("Could not obtain coordinates.")
            return None
            
        latitude, longitude = coordinates
        max_retries = 3  # Reduced from 50. 50 retries with 5s sleep = 4+ minutes hangtime!
        attempts = 0

        while attempts < max_retries:
            try:
                url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={latitude}&lon={longitude}"
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                attempts += 1
                print(f"Attempt {attempts} to retrieve weather data failed: {e}")
                t.sleep(2)

        print("Max retries reached. Could not fetch weather data.")
        return None

    def weather_data(self):
        """
        Extract and process specific weather parameters from API response.
        """
        # Short-circuit if this instance has already run calculations once in this lifecycle
        if self._processed_data is not None:
            return self._processed_data

        cache_key = f"weather_data_{self.country_code}_{self.city_code}"
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            self._processed_data = cached_result
            return cached_result

        json_data = self.weather_json()
        if json_data is None:
            return (None, None, None, None, None, None, None)

        timeseries = json_data['properties']['timeseries']
        if not timeseries:
            print("No forecast data available.")
            return (None, None, None, None, None, None, None)

        # --- Current hour data ---
        current = timeseries[0]['data']['instant']['details']
        air_temperature = current['air_temperature']
        relative_humidity = current['relative_humidity']
        wind_speed = current['wind_speed']

        # --- Weather symbol & description ---
        next_1 = timeseries[0]['data'].get('next_1_hours', {})
        symbol_code = next_1.get('summary', {}).get('symbol_code')
        weather_description = self.WEATHER_CONDITIONS.get(symbol_code, "Unknown")

        # --- 24-hour temperature forecast ---
        temp_24h = [
            timeseries[i]['data']['instant']['details']['air_temperature'] 
            for i in range(min(24, len(timeseries)))
        ]

        # --- Weekly data processing (keeping your existing structure) ---
        weekly_data = {}
        for entry in timeseries:
            time_str = entry["time"]
            date_key = time_str

            instant = entry["data"]["instant"]["details"]
            current_temp = instant.get("air_temperature")
            wind_sp = instant.get("wind_speed")
            pressure = instant.get("air_pressure_at_sea_level")
            
            precip, symbol = None, None
            if 'next_1_hours' in entry['data']:
                next_1_hours_data = entry["data"].get("next_1_hours", {})
                precip = next_1_hours_data.get("details", {}).get("precipitation_amount")
                symbol = next_1_hours_data.get("summary", {}).get("symbol_code")
            elif 'next_6_hours' in entry['data']:
                next_6_hours_data = entry["data"].get("next_6_hours", {})
                symbol = next_6_hours_data.get("summary", {}).get("symbol_code")
                precip = next_6_hours_data.get("details", {}).get("precipitation_amount")

            record = {
                "time": time_str, "temp": current_temp, "wind_speed": wind_sp,
                "pressure": pressure, "precip": precip, "symbol": symbol,
            }

            if date_key not in weekly_data:
                weekly_data[date_key] = {"entries": [], "min_temp": None, "max_temp": None}

            weekly_data[date_key]["entries"].append(record)

            if current_temp is not None:
                if (weekly_data[date_key]["min_temp"] is None or current_temp < weekly_data[date_key]["min_temp"]):
                    weekly_data[date_key]["min_temp"] = current_temp
                if (weekly_data[date_key]["max_temp"] is None or current_temp > weekly_data[date_key]["max_temp"]):
                    weekly_data[date_key]["max_temp"] = current_temp
            
        weekly = {}
        a = list(weekly_data.keys())
        for i, _ in enumerate(weekly_data): 
             if a[i][:10] in weekly:
                continue
             else:
                weekly[a[i][:10]] = weekly_data[a[i]]

        processed_data = (air_temperature, relative_humidity, wind_speed, weather_description, symbol_code, temp_24h, weekly)
        
        # Save processed payload to cache for 1 hour
        cache.set(cache_key, processed_data, timeout=3600)
        self._processed_data = processed_data
        
        return processed_data

    def feels_like_temperature(self):
        """
        Calculate feels-like temperature based on environmental conditions.
        """
        data = self.weather_data()  # Uses instance tracker or cache hit seamlessly now
        temperature, humidity, wind_speed, *_ = data
        if temperature is None:
            return None

        temp_f = (temperature * 9 / 5) + 32

        if temperature >= 27 and humidity is not None:
            hi_f = (
                -42.379 + 2.04901523 * temp_f + 10.14333127 * humidity
                - 0.22475541 * temp_f * humidity - 0.00683783 * temp_f ** 2
                - 0.05481717 * humidity ** 2 + 0.00122874 * temp_f ** 2 * humidity
                + 0.00085282 * temp_f * humidity ** 2 - 0.00000199 * temp_f ** 2 * humidity ** 2
            )
            return round((hi_f - 32) * 5 / 9, 2)

        elif temperature <= 10 and wind_speed is not None:
            wc_f = (
                35.74 + 0.6215 * temp_f - 35.75 * (wind_speed ** 0.16)
                + 0.4275 * temp_f * (wind_speed ** 0.16)
            )
            return round((wc_f - 32) * 5 / 9, 2)

        return round(temperature, 2)
