from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .models import UserProfile  # Import UserProfile model

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        # Authenticate using username
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            
            if user is not None:
                auth_login(request, user)
                return redirect('home')
            else:
                pass  # Handle error
        except User.DoesNotExist:
            pass  # Handle error

    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        # Get form data
        email = request.POST.get('email')
        fullname = request.POST.get('fullname')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        repassword = request.POST.get('repassword')

        if password == repassword:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(username=email, email=email, password=password)
                userprofile = UserProfile.objects.create(user=user, fullname=fullname, email=email, phone=phone)
                user.save()
                userprofile.save()
                return redirect('login')
            else:
                pass  # Handle error: user already exists
        else:
            pass  # Handle error: passwords do not match

    return render(request, 'register.html')

def logout_view(request):
    auth_logout(request)
    return redirect('home')

def home(request):
        
    context = {
    }
    return render(request, 'home.html', context)
