from geopy.geocoders import Nominatim
import requests
from datetime import datetime

# Define the city and country codes for the desired location (Kanpur, India)
city_code = "232101"
country_code = "IN"

# Get the current time
time_data = datetime.now()
time = time_data.strftime("%I:%M %p")

# Get the current month
current_month = time_data.strftime("%B")

# Get current year
current_year = time_data.strftime("%Y")

# Initialize the geolocator with a user agent
geolocator = Nominatim(user_agent="pape") # Replace with your app name

# Geocode the city and country to get latitude and longitude
location = geolocator.geocode(f"{city_code}, {country_code}")
latitude,longitude = location.latitude, location.longitude

# Function to fetch weather data from the MET Norway API
def get_metno_weather(latitude, longitude):
    # Construct the API URL with latitude and longitude
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={latitude}&lon={longitude}"
    # Define the required User-Agent header
    headers = {
        'User-Agent': 'pape_weather/1.0 (shobhasharm123com@gmail.com)'
    }
    try:
        # Send a GET request to the API
        response = requests.get(url, headers=headers)
        # Raise an exception for HTTP errors (4xx or 5xx)
        response.raise_for_status()
        # Parse the JSON response
        weather_data = response.json()
        return weather_data
    except requests.exceptions.RequestException as e:
        # Print an error message if fetching data fails
        print(f"Error fetching weather data: {e}")
        return None

# Check if latitude and longitude were successfully obtained
if latitude and longitude:
    # Fetch weather data using the coordinates
    weather = get_metno_weather(latitude, longitude)
    # Process the weather data if it was successfully retrieved
    if weather:
        # Extract the time series forecast data
        time_series = weather.get('properties', {}).get('timeseries', [])
        # Check if time series data exists
        if time_series:
            # Get the latest forecast (current or nearest future)
            latest_data = time_series[0].get('data', {})
            instant_details = latest_data.get('instant', {}).get('details', {})
            temperature = instant_details.get('air_temperature')
        else:
            print("No weather forecast data found.")
    else:
        print("Failed to retrieve weather data from MET Norway.")
if __name__ == "__main__":
    print(longitude , latitude)