from django.urls import path
from . import views
urlpatterns = [ 
    # This path defines the URL pattern for the homepage of the application.
    # The empty string '' signifies the root URL (e.g., http://yourdomain.com/).
    # When a user accesses the root URL, the 'home' view function from the 'views.py' file will be executed.
    path('login/', views.login,name="login"),
    path('signup/', views.sign_up, name="sign_up" ),
    path('logout/', views.logout_view, name='logout'),
    # path('verify-otp/resend/', views.resend_otp_view, name='resend_otp'),
    path('verify-otp/', views.verify_otp_extension_view, name='verify_otp_extension'),
]
