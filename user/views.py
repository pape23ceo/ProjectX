import email
import datetime
from django import forms
from .forms import SignUpForm
from django.urls import reverse
from django.conf import settings
from rest_framework import generics
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from .serializers import UserSerializer
from django.contrib.auth.models import User
from rest_framework.response import Response
from django.shortcuts import render, redirect
from rest_framework.permissions import IsAuthenticated ,AllowAny 
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.forms import UserCreationForm
from .models import EmailOTP , UserProfile
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
# Create your views here.

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get('access_token')
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
    
class CreateUserView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer 
    permission_classes = [AllowAny] 

class CustomTokenObtainPairView(TokenObtainPairView):
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        # Call the parent to validate credentials and get tokens
        response = super().post(request, *args, **kwargs)

        # If login successful (status 200), set cookies and redirect
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            redirect_response = redirect('home')   # make sure 'home' URL exists
            redirect_response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=datetime.timedelta(minutes=30)   # match ACCESS_TOKEN_LIFETIME
            )
            redirect_response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=datetime.timedelta(days=1)       # match REFRESH_TOKEN_LIFETIME
            )
            return redirect_response

        # If login failed, re-render the login template with errors
        return render(request, self.template_name, {'errors': response.data})
def logout_view(request):
    logout(request)
    return redirect('login') 
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Save user but keep inactive until email verified
            user = form.save(commit=False)
            user.is_active = False
            user.email = form.cleaned_data['email']
            if User.objects.filter(email=user.email).exists():
                raise forms.ValidationError("A user with this email already exists.")
            user.save()

            # Generate OTP and send email
            otp_code = EmailOTP.generate_otp(user)
            send_mail(
                'Your verification code',
                f'Your OTP is {otp_code}. It expires in 10 minutes.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            # Store user id in session so we can identify them on the verification page
            request.session['verify_user_id'] = user.id
            return redirect('verify_email')   # we'll create this URL

    else:
        form = SignUpForm()
    return render(request, 'sign-up.html', {'form': form})

def verify_email_view(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect('signup')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('signup')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        try:
            otp_obj = EmailOTP.objects.get(user=user)
        except EmailOTP.DoesNotExist:
            return render(request, 'verify_otp.html', {'error': 'No OTP found. Please sign up again.'})

        # Check expiry (e.g., 10 minutes)
        if otp_obj.created_at + datetime.timedelta(minutes=10) < datetime.datetime.now(datetime.timezone.utc):
            return render(request, 'verify_otp.html', {'error': 'OTP expired. Please sign up again.'})

        if otp_obj.otp == entered_otp:
            # Activate user and clean up
            user.is_active = True
            user.save()
            otp_obj.delete()

            # Generate JWT tokens and set cookies, then redirect home
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = redirect('home')
            response.set_cookie('access_token', access_token, httponly=True, samesite='Lax')
            response.set_cookie('refresh_token', refresh_token, httponly=True, samesite='Lax')
            # Clear the session key
            del request.session['verify_user_id']
            return response
        else:
            return render(request, 'verify_otp.html', {'error': 'Invalid OTP'})

    return render(request, 'verify_otp.html')

def resend_otp_view(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect('signup')
    user = User.objects.get(id=user_id)
    otp_code = EmailOTP.generate_otp(user)
    send_mail(
        'Your verification code',
        f'Your OTP is {otp_code}. It expires in 10 minutes.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    return render(request, 'verify_email.html', {'message': 'OTP resent'})

def home_view(request):
    return render(request, 'home.html')