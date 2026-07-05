from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
urlpatterns = [ 
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('token/', TokenObtainPairView.as_view(), name='token'),
    path('token_refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('home/', views.home_view, name='home'),
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
]
