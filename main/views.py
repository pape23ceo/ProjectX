# --- Importing important files and modules ---
from django.shortcuts import render
from django.http import HttpResponse
from . import weather_api
# from django.contrib.auth.decorators import login_required

# @login_required
def home(request):
    # Initialize default values
    context = {
        'city': "--:--",
        'date': "--",
        'temp': "--",
        'times': "--:--",
        'month': "--",
        'feels_like': '--',
        'wind': '--',
        'humidity': "--",
        "path": "images/weather_pic/clearsky_day.svg",
        'error': None
    }

    # Handle GET request
    if request.method == 'GET':
        weather_location_code = request.GET.get("coordinates")  # Get coordinates from the request
        weather_json = None
        if weather_location_code:
            try:
                latitude, longitude = weather_location_code.split(",")
                x = weather_api.Weather(latitude=latitude, longitude=longitude)
                weather_json = x.weather_json()
                
            except ValueError:
                context['error'] = "Invalid pincode format. Use: COUNTRY_CODE,PINCODE"
            except Exception as e:
                context['error'] = f"Weather data fetch failed: {str(e)}"

    return render(request, 'index.html', {'backend_json': weather_json})

def weather_search(request):
    return render(request, 'main.html')