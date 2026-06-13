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
        weather_location_code = request.GET.get("pincode")
        
        if weather_location_code:
            try:
                contry_code, pin_code = weather_location_code.split(",")
                x = weather_api.Weather(country_code=contry_code, city_code=pin_code)

                air_temperature, relative_humidity, wind_speed, _, symbol , hours_temp, weekly= x.weather_data()
                feels_like = x.feels_like_temperature()

                # Update context with fetched data
                context.update({
                    'temp': air_temperature,
                    'feels_like': feels_like,
                    'wind': wind_speed,
                    'humidity': relative_humidity,
                    "path": f"images/weather_pic/{symbol}.svg",
                    "weekly" : weekly,
                    "hours_temp": hours_temp,
                })
                
            except ValueError:
                context['error'] = "Invalid pincode format. Use: COUNTRY_CODE,PINCODE"
            except Exception as e:
                context['error'] = f"Weather data fetch failed: {str(e)}"

    return render(request, 'index.html', context)
