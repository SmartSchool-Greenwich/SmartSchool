from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .models import ContributionFiles, UserProfile  ,Faculties,Contributions
from .forms import ContributionFileForm ,UserRegistrationForm,UserProfileForm,ContributionForm
from django.contrib.auth.decorators import login_required

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
    faculties = Faculties.objects.all()
    context = { 'faculties':faculties
    }
    return render(request, 'home.html', context)



@login_required
def file_upload_view(request):
    faculties = Faculties.objects.all()  # If needed for the form
    if request.method == 'POST':
        contribution_form = ContributionForm(request.POST)
        if contribution_form.is_valid():
            contribution = contribution_form.save(commit=False)
            contribution.faculty = contribution_form.cleaned_data['faculty']  # Assuming faculty is a field in your form
            contribution.save()
            contribution.user.add(request.user.userprofile)  # Associate the current user's profile with the contribution

            # Handling file uploads
            files = request.FILES.getlist('word') + request.FILES.getlist('img')
            for file in files:
                ContributionFiles.objects.create(
                    word=file if file.name.endswith('.docx') or file.name.endswith('.doc') else None,
                    img=file if not (file.name.endswith('.docx') or file.name.endswith('.doc')) else None,
                    contribution=contribution
                )

            return redirect('success_url')  # Redirect to a success page.
    else:
        contribution_form = ContributionForm()

    return render(request, 'upload.html', {
        'contribution_form': contribution_form,
        'faculties': faculties
    })

def upload_success(request):
    return render(request, 'upload_success.html')




def craete_account(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            # Create a new user object but avoid saving it yet
            new_user = user_form.save(commit=False)
            # Set the chosen password
            new_user.set_password(user_form.cleaned_data['password'])
            # Save the User object
            new_user.save()
            # Create the user profile
            new_profile = profile_form.save(commit=False)
            new_profile.user = new_user
            new_profile.save()
            # Add the selected role to the user's profile
            role = user_form.cleaned_data['role']
            new_profile.roles.add(role)
            new_profile.save()
            return redirect('login')  # Redirect to a login page after successful registration
    else:
        user_form = UserRegistrationForm()
        profile_form = UserProfileForm()
    return render(request, 'create_account.html', {'user_form': user_form, 'profile_form': profile_form})




def faculty_files(request, faculty_id):
    # Fetch the specific faculty
    faculty = get_object_or_404(Faculties, pk=faculty_id)
    # Fetch contributions associated with the faculty
    contributions = Contributions.objects.filter(faculty=faculty)
    # Fetch files associated with those contributions
    files = ContributionFiles.objects.filter(contribution__in=contributions).distinct()
    
    return render(request, 'faculty_file.html', {'faculty': faculty, 'files': files})