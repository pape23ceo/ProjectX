from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import views as auth_view
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth import login as auth_login 
from django.contrib.auth import views as auth_view
from django_otp.plugins.otp_email.models import EmailDevice
from django_otp import devices_for_user
# Render login page
def login(request):
    return auth_view.LoginView.as_view(template_name="login.html")(request)
# Render sign-up page

def sign_up(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # 1. Standard Username Check
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'sign-up.html')
            
        # 2. CHECK ACTIVE EMAIL: Block if the email is already verified & active
        if User.objects.filter(email=email, is_active=True).exists():
            messages.error(request, "An account with this email address already exists.")
            return render(request, 'sign-up.html')
            
        # 3. CLEAN UP INACTIVE EMAIL: If someone signed up with this email before 
        # but never verified their OTP, delete that stale account so they can try again.
        User.objects.filter(email=email, is_active=False).delete()
        
        # 4. Now it is completely safe to create the new user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False  # Keep them locked until OTP is verified
        user.save()
        
        # 5. Set up the official EmailDevice for django-otp
        device, created = EmailDevice.objects.get_or_create(user=user, name="default")
        device.generate_challenge()  # Automatically generates and emails the OTP
        
        request.session['verification_user_id'] = user.id
        return redirect('verify_otp_extension')
        
    return render(request, 'sign-up.html')

def verify_otp_extension_view(request):
    user_id = request.session.get('verification_user_id')
    if not user_id:
        return redirect('sign_up')  # If no user ID in session, redirect to sign-up page
        
    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        
        # Fetch the email devices attached to this specific user
        user_devices = devices_for_user(user)
        verified = False
        
        for device in user_devices:
            if isinstance(device, EmailDevice):
                # The library checks matching values, expiration dates, and brute force blocks internally!
                if device.verify_token(entered_otp):
                    verified = True
                    break
                    
        if verified:
            user.is_active = True
            user.save()
            auth_login(request, user)
            del request.session['verification_user_id']
            messages.success(request, "Successfully verified with django-otp!")
            return redirect('home')
        else:
            messages.error(request, "The code provided is incorrect or has expired.")
            
    return render(request, 'verify_otp.html')

def logout_view(request):
    logout(request)
    return redirect('login')   # redirect to login page