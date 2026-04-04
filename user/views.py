from django.shortcuts import render, redirect ,HttpResponse
from django.contrib.auth.forms import UserCreationForm 
from django.contrib import messages
from django.contrib.auth import views as auth_view
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
# Render login page
def login(request):
    return auth_view.LoginView.as_view(template_name="login.html")(request)
# Render sign-up page

def sign_up(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Save the user to database
            username = form.cleaned_data.get('username')
            messages.success(request, f"Your account has been created as {username}!")
            return redirect("home")
        else:
            messages.error(request,"Please enter right crecidetial for your account")
            
    else:
        form = UserCreationForm()

    context = {
        "form": form
    }
    return render(request, 'sign-up.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')   # redirect to login page