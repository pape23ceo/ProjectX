import datetime
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils import timezone

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .forms import SignUpForm
from .models import EmailOTP, UserProfile
from .serializers import UserSerializer

User = get_user_model()


# Custom JWT Authentication reading tokens from HTTP-Only Cookies
class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get('access_token')
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token


# Helper function to set JWT HTTP-Only Cookies consistently
def set_jwt_cookies(response, user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        max_age=30 * 60  # 30 minutes in seconds
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        max_age=24 * 60 * 60  # 1 day in seconds
    )
    return response


class CreateUserView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        # 1. Bind form/request data to SimpleJWT serializer directly
        serializer = self.get_serializer(data=request.data)

        try:
            # 2. Validate credentials. Throws exception if login fails.
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError, APIException) as exc:
            # 3. Catch login failure and re-render login.html with error message
            error_detail = getattr(exc, 'detail', {'detail': 'Invalid credentials'})
            return render(request, self.template_name, {'errors': error_detail}, status=400)

        # 4. Extract the validated user object attached by SimpleJWT
        user = serializer.user

        # 5. Redirect to home and attach HTTP-Only cookies
        redirect_response = redirect('weather_search')
        return set_jwt_cookies(redirect_response, user)


def logout_view(request):
    logout(request)
    response = redirect('login')
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Check duplicate email properly without crashing
            if User.objects.filter(email=email).exists():
                form.add_error('email', "A user with this email already exists.")
                return render(request, 'sign-up.html', {'form': form})

            user = form.save(commit=False)
            user.is_active = False
            user.email = email
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

            request.session['verify_user_id'] = user.id
            return redirect('verify_email')
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

        # Check expiry (10 minutes) using timezone.now()
        if otp_obj.created_at + datetime.timedelta(minutes=10) < timezone.now():
            return render(request, 'verify_otp.html', {'error': 'OTP expired. Please sign up again.'})

        if otp_obj.otp == entered_otp:
            user.is_active = True
            user.save()
            otp_obj.delete()

            response = redirect('home')
            response = set_jwt_cookies(response, user)

            if 'verify_user_id' in request.session:
                del request.session['verify_user_id']
                
            return response
        else:
            return render(request, 'verify_otp.html', {'error': 'Invalid OTP'})

    return render(request, 'verify_otp.html')


def resend_otp_view(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect('signup')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('signup')

    otp_code = EmailOTP.generate_otp(user)
    send_mail(
        'Your verification code',
        f'Your OTP is {otp_code}. It expires in 10 minutes.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    return render(request, 'verify_otp.html', {'message': 'OTP resent successfully.'})


def home_view(request):
    return render(request, 'home.html')