from django.urls import path
from . import views

urlpatterns = [
    # This path defines the URL pattern for the homepage of the application.
    # The empty string '' signifies the root URL (e.g., http://yourdomain.com/).
    # When a user accesses the root URL, the 'home' view function from the 'views.py' file will be executed.
    path('', views.home),
]