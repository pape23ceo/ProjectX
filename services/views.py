from django.shortcuts import render
from django.http import HttpResponse
from . import database

# Import the temperature variable from the database module
temp = database.temperature
# Import the current month variable from the database module
month = database.current_month
# Import the time variable from the database module
time = database.time
# Import the current year variable from the database module
year = database.current_year

# Create a dictionary to hold the data that will be passed to the template
context = {
    'temp': temp,       # Temperature value
    'times': time,      # Current time
    'month': month,     # Current month
    'year': year,       # Current year
}

# Define the view function for the home page
def home(request):
    # Render the 'index.html' template and pass the 'context' dictionary
    return render(request, 'index.html', context)