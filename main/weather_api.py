import requests
from django.core.cache import cache

class Weather:
    headers = {
        'User-Agent': 'pape_weather_website/1.0 (papwhv@outlook.com)'
    }

    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def weather_json(self):
        """
        Fetch raw weather data using cached coordinates and retry logic.
        """

        if self.latitude and self.longitude is None:
            print("Could not obtain coordinates.")
            return None
        
        cache_key = f"weather_forecast_{self.latitude}_{self.longitude}"
        cached_json = cache.get(cache_key)

        if not cached_json:
            try:
                url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={self.latitude}&lon={self.longitude}"
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                weather_json = response.json()
                cache.set(cache_key, weather_json, timeout=3600)
                return weather_json
              
            except Exception as e:
                return None
            
        return cached_json