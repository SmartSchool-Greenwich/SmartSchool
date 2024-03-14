from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import ContributionFiles, UserProfile, Faculties, Contributions, Role,AcademicYear, Comment
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from .forms import CommentForm, FileForm, RoleForm
from django.urls import reverse
import zipfile
from io import BytesIO
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            pass
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            pass

    return render(request, 'login.html')

def register_view(request):
    faculties = Faculties.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        fullname = request.POST.get('fullname')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        repassword = request.POST.get('repassword')
        faculty_id = request.POST.get('faculty', None)

        if all([username, fullname, phone, password, repassword]):
            if password == repassword:
                if User.objects.filter(username=username).exists():
                    return redirect('register')
                else:
                    user = User.objects.create_user(username=username, password=password, email=email)
                    faculty = Faculties.objects.get(id=faculty_id) if faculty_id else None
                    
                    userprofile = UserProfile(user=user, fullname=fullname, email=email, phone=phone, faculty=faculty)
                    userprofile.save()
                    return redirect('login')
            else:
                return redirect('register')
        
    return render(request, 'register.html', {'faculties': faculties})

def logout_view(request):
    logout(request)
    return redirect('home')

def home(request):
    can_upload = True
    is_admin = False
    is_cordinator = False
    is_director = False
    is_student = False
    is_guest = False
    show_faculties = True  
    faculties = Faculties.objects.none() 

    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
            faculty = user_profile.faculty
            # academic_year = faculty.academicYear if faculty else None
            roles = [role.name for role in user_profile.roles.all()]

            # if academic_year and timezone.now() < academic_year.closure:
            #     can_upload = True

            if "marketing director" in roles:
                faculties = Faculties.objects.all()
                is_director = True
            elif "admin" in roles:
                faculties = Faculties.objects.all()
                is_admin = True
            elif "marketing cordinator" in roles:
                faculties = Faculties.objects.filter(id=faculty.id) if faculty else Faculties.objects.none()
                is_cordinator = True
            elif "guest" in roles:
                faculties = Faculties.objects.all()
                is_guest = True
            else:
                is_student = True
                show_faculties = False

        except UserProfile.DoesNotExist:
            can_upload = True
            show_faculties = False
    else:   
        show_faculties = False
        
    context = {
        'faculties': faculties,
        'can_upload': can_upload,
        'is_admin': is_admin,
        'is_cordinator': is_cordinator,
        'is_director': is_director,
        'is_student': is_student,
        'is_guest': is_guest,
        'show_faculties': show_faculties,
    }
    return render(request, 'home.html', context)


def file_upload_view(request):
    faculties = None  # Initialize faculties to None or an empty list
    
    if request.user.is_authenticated:
        user_profile = None
        faculties = None
        try:
            is_student = True
            user_profile = request.user.userprofile
            if user_profile.academic_Year and user_profile.academic_Year.closure > timezone.now():
                # User has a valid AcademicYear, so you can continue to the upload logic.
                user_faculty = user_profile.faculty
                if user_faculty:
                    faculties = Faculties.objects.filter(id=user_faculty.id)
            else:
                # Redirect to the page for entering AcademicYear code if AcademicYear is not valid
                return redirect('enter_academic_year_code_url')
        except UserProfile.DoesNotExist:
            # Handle the case where the user does not have a profile, according to your application's requirements
            pass
        
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        faculty_id = request.POST.get('faculty')
        term = request.POST.get('term') == 'on'
    
        try:
            faculty = Faculties.objects.get(id=faculty_id)
        # Retrieve the current AcademicYear from the user's profile
            current_academic_year = None
            if request.user.userprofile.academic_Year:
                current_academic_year = request.user.userprofile.academic_Year

        # Create the contribution with the current AcademicYear
            contribution = Contributions.objects.create(
                title=title,
                content=content,
                faculty=faculty,
                term=term,
                academic_Year=current_academic_year  # Assign the AcademicYear here
            )
            contribution.user.add(request.user.userprofile)
        
        # Initialize the ContributionFiles instance outside the loop
            contribution_file = ContributionFiles(contribution=contribution)
        # Handle file uploads
            files_uploaded = False  # Flag to check if any valid file was uploaded
            for file in request.FILES.getlist('word') + request.FILES.getlist('img'):
                if file.name.endswith('.doc') or file.name.endswith('.docx'):
                # Assuming 'word' field should only have one file
                    if not contribution_file.word:
                        contribution_file.word = file
                        files_uploaded = True
            # Exclude PDF files from being uploaded to 'img' field
                elif not file.name.endswith('.pdf') and not contribution_file.img:
                    contribution_file.img = file
                    files_uploaded = True
        
            if files_uploaded:
                contribution_file.save()
            
            #sendmail
            marketing_coordinator_role = Role.get_marketing_coordinator_role()
            if marketing_coordinator_role:
                coordinator_profiles = UserProfile.objects.filter(
                    roles=marketing_coordinator_role,
                    faculty=faculty
                )

                recipient_list = [coordinator.email for coordinator in coordinator_profiles if coordinator.email]
                if recipient_list:
                    send_mail(
                        subject='New Contribution Submitted',
                        message=f'A new contribution "{title}" has been submitted to {faculty.name} by {request.user.userprofile.fullname}.',
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=recipient_list,
                    )


            return redirect('success_url') 
        except Faculties.DoesNotExist:
            return redirect('home')
        except Exception as e:
            print(e) 
            return redirect('home')
    
    else:
        context = {'faculties': faculties,
                   'is_student': is_student}
        
    return render(request, 'upload.html', context)


def enter_academic_year_code(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            academic_year = AcademicYear.objects.get(code=code)
            user_profile = request.user.userprofile
            user_profile.academic_Year = academic_year
            user_profile.save()
            if user_profile.academic_Year and user_profile.academic_Year.closure < timezone.now():
                # User has a valid AcademicYear, so you can continue to the upload logic.
                messages.error(request, 'You can not enroll to expired Academic Year.')
            return redirect('file_upload')  # Assuming this is the URL name for file upload view
        except AcademicYear.DoesNotExist:
            messages.error(request, 'Invalid code or Academic Year has expired.')
    
    return render(request, 'enter_academic_year_code.html')

def update_contribution(request, pk):
    contribution = get_object_or_404(Contributions, pk=pk)

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        term = request.POST.get('term') == 'on'
        contribution.title = title
        contribution.content = content
        contribution.term = term
        contribution.save()

        word_file = request.FILES.get('word', None)
        img_file = request.FILES.get('img', None)
        if word_file or img_file:
            contribution_files, created = ContributionFiles.objects.get_or_create(contribution=contribution)
            if word_file:
                contribution_files.word = word_file
            if img_file:
                contribution_files.img = img_file
            contribution_files.save()

        return redirect('my_contributions')  

    contribution_files = ContributionFiles.objects.filter(contribution=contribution).first()
    context = {
        'contribution': contribution,
        'contribution_files': contribution_files,
    }
    return render(request, 'update_contribution.html', context)

@login_required
def delete_contribution(request, pk):
    contribution = get_object_or_404(Contributions, pk=pk)
    if request.method == 'GET': 
        contribution.delete()
        return redirect('my_contributions')
    else:
        return HttpResponse('Method not allowed', status=405) 


def upload_success(request):
    return render(request, 'upload_success.html')

def create_account(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        fullname = request.POST['fullname']
        phone = request.POST.get('phone', '')
        role_id = request.POST['role']
        faculty_id = request.POST.get('faculty', None) 

        if password == confirm_password:
            user = User.objects.create_user(username=username, password=password)

            new_profile = UserProfile(user=user, fullname=fullname, phone=phone)

            if faculty_id:
                try:
                    faculty = Faculties.objects.get(id=faculty_id)
                    new_profile.faculty = faculty
                except Faculties.DoesNotExist:
                    pass  

            new_profile.save()

            selected_role = Role.objects.get(id=role_id)
            new_profile.roles.add(selected_role)

            return redirect('login')
    else: 
        roles = Role.objects.all()
        faculties = Faculties.objects.all() 
        return render(request, 'create_account.html', {'roles': roles, 'faculties': faculties})




def faculty_files(request, faculty_id):
    is_guest = False
    is_director = False
    user_profile = get_object_or_404(UserProfile, user=request.user)
    show_faculties = True 
    faculty = user_profile.faculty
    faculties = Faculties.objects.filter(id=faculty.id) if faculty else Faculties.objects.none() 
    if request.user.is_authenticated:
        # academic_year = faculty.academicYear if faculty else None
        roles = [role.name for role in user_profile.roles.all()]

        # if academic_year and timezone.now() < academic_year.closure:
        if "marketing director" in roles:
            is_director = True
            faculties = Faculties.objects.all() 
        elif "guest" in roles:
            is_guest = True
            faculties = Faculties.objects.all() 
    faculty = get_object_or_404(Faculties, pk=faculty_id)
    contributions = Contributions.objects.filter(faculty_id=faculty_id)
    files = ContributionFiles.objects.filter(contribution__in=contributions).distinct()
    comment_form = CommentForm()   

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            contribution_id = request.POST.get('contribution_id')
            try:
                contribution = Contributions.objects.get(id=contribution_id)
                new_comment = comment_form.save(commit=False)
                new_comment.contribution = contribution

                user_profile, created = UserProfile.objects.get_or_create(user=request.user)
                new_comment.user = user_profile
                new_comment.save()
                return redirect('faculty_files', faculty_id=faculty_id)
            except Contributions.DoesNotExist:
                return HttpResponse("Contribution does not exist", status=404)
    return render(request, 'faculty_file.html', {'faculty': faculty, 
                                                 'files': files, 
                                                 'is_guest': is_guest,
                                                 'contributions': contributions,
                                                 'faculties': faculties,
                                                 'show_faculties': show_faculties,
                                                 'is_director': is_director})

def show_contributions(request):
    is_director = False
    show_faculties = True 
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if request.user.is_authenticated:
        # academic_year = faculty.academicYear if faculty else None
        roles = [role.name for role in user_profile.roles.all()]

        # if academic_year and timezone.now() < academic_year.closure:
        if "marketing director" in roles:
            is_director = True
            faculties = Faculties.objects.all() 

    contributions = Contributions.objects.filter(status="approved")
    
    return render(request, 'show_contribution.html', {'contributions': contributions,
                                                      'is_director': is_director,
                                                      'show_faculties': show_faculties,
                                                      'faculties' : faculties})


def download_selected_contributions(request):
    contribution_ids = request.POST.getlist('contribution_ids')
    files = ContributionFiles.objects.filter(contribution__id__in=contribution_ids)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            if file.word:
                zip_file.write(file.word.path, arcname=file.word.name)
            if file.img:
                zip_file.write(file.img.path, arcname=file.img.name)

    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="selected_contributions.zip"'

    return response


def update_profile(request):
    user_profile = get_object_or_404(UserProfile, user=request.user.userprofile)
    show_faculties = True 
    faculty = user_profile.faculty
    faculties = Faculties.objects.none() 
    is_cordinator = False
    is_director = False
    is_student = False

    if request.user.is_authenticated:
        # academic_year = faculty.academicYear if faculty else None
        roles = [role.name for role in user_profile.roles.all()]

        # if academic_year and timezone.now() < academic_year.closure:
        if "marketing director" in roles:
            faculties = Faculties.objects.all()
            is_director = True
        elif "marketing cordinator" in roles:
            faculties = Faculties.objects.filter(id=faculty.id) if faculty else Faculties.objects.none()
            is_cordinator = True
        else:
            is_student = True
            show_faculties = False

    if request.method == 'POST':
        user_profile.fullname = request.POST.get('fullname', '')
        user_profile.email = request.POST.get('email', '')
        user_profile.phone = request.POST.get('phone', '')
        user_profile.save()
        return redirect('home')
    else:
        return render(request, 'update_profile.html', {'user_profile': user_profile,
                                                       'faculties': faculties,
                                                       'show_faculties': show_faculties,
                                                       'is_cordinator': is_cordinator,
                                                       'is_director': is_director,
                                                       'is_student': is_student})

def contributions_detail(request, contribution_id):
    contribution = get_object_or_404(Contributions, id=contribution_id)
    comments = Comment.objects.filter(contribution=contribution)
    can_update = False 
    user_profile = request.user.userprofile
    show_faculties = True 
    faculties = Faculties.objects.none() 
    faculty = user_profile.faculty
    is_cordinator = False
    is_student = False 
    
    if request.user.is_authenticated:
        # academic_year = faculty.academicYear if faculty else None
        roles = [role.name for role in user_profile.roles.all()]

        # if academic_year and timezone.now() < academic_year.closure:
        if "marketing cordinator" in roles:
            faculties = Faculties.objects.filter(id=faculty.id) if faculty else Faculties.objects.none()
            is_cordinator = True
        else:
            is_student = True
            show_faculties = False

        try:
            user_profile = request.user.userprofile
            faculty = user_profile.faculty
            academic_year = user_profile.academic_Year
            if academic_year and timezone.now() < academic_year.finalClosure:
                can_update = True
        except UserProfile.DoesNotExist:
            can_update = False 

    if request.method == "POST":
        if 'comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                new_comment = comment_form.save(commit=False)
                new_comment.contribution = contribution
                new_comment.user = request.user.userprofile
                new_comment.save()
                return HttpResponseRedirect(reverse('contribution_detail', args=[contribution_id]))

        elif request.FILES:
            file_form = FileForm(request.POST, request.FILES)
            if file_form.is_valid():
                new_file = file_form.save(commit=False)
                new_file.contribution = contribution
                new_file.save()
                return HttpResponseRedirect(reverse('contribution_detail', args=[contribution_id]))
    else:
        comment_form = CommentForm()
        file_form = FileForm()

    return render(request, 'contributions_detail.html', {
        'contribution': contribution,
        'comments': comments,
        'comment_form': comment_form,
        'file_form': file_form,
        'can_update': can_update,
        'show_faculties': show_faculties,
        'is_cordinator': is_cordinator,
        'is_student': is_student,
        'faculties': faculties,
    })    



def my_contributions(request):
    is_student = True
    user_profile = UserProfile.objects.get(user=request.user)
    contributions = Contributions.objects.filter(user=user_profile).prefetch_related('faculty', 'files')
    can_update = True
    
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
            faculty = user_profile.faculty
            academic_year = user_profile.academic_Year
            if user_profile.academic_Year:
                if academic_year and timezone.now() > academic_year.finalClosure:
                    can_update = False

        except UserProfile.DoesNotExist:
            can_update = True

    
    context = {
        'can_update': can_update,
        'contributions': contributions,
        'is_student': is_student
    }
    return render(request, 'my_contribution.html', context)



def list_faculties(request):
    faculties = Faculties.objects.all()
    return render(request, 'list_faculties.html', {'faculties': faculties})


def remove_faculty(request, faculty_id):
    faculty = get_object_or_404(Faculties, pk=faculty_id)
    faculty.delete()
    return redirect('list_faculties')



@login_required
def user_profile(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    show_faculties = True 
    faculty = user_profile.faculty
    faculties = Faculties.objects.none() 
    is_cordinator = False
    is_director = False
    is_student = False

    if request.user.is_authenticated:
        # academic_year = faculty.academicYear if faculty else None
        roles = [role.name for role in user_profile.roles.all()]

        # if academic_year and timezone.now() < academic_year.closure:
        if "marketing director" in roles:
            faculties = Faculties.objects.all()
            is_director = True
        elif "marketing cordinator" in roles:
            faculties = Faculties.objects.filter(id=faculty.id) if faculty else Faculties.objects.none()
            is_cordinator = True
        else:
            is_student = True
            show_faculties = False

    return render(request, 'profile.html', {'user_profile': user_profile,
                                            'faculties': faculties,
                                            'show_faculties': show_faculties,
                                            'is_cordinator': is_cordinator,
                                            'is_director': is_director,
                                            'is_student': is_student})

#academic
def list_academic_years(request):
    academic_years = AcademicYear.objects.all()
    return render(request, 'list_academic_years.html', {'academic_years': academic_years})


def create_academic_year(request):
    page = "create"
    if request.method == "POST":
        closure = request.POST.get('closure')
        finalClosure = request.POST.get('finalClosure')
        AcademicYear.objects.create(closure=closure, finalClosure=finalClosure)
        return redirect('list_academic_years')
    context = {
        'page' : page,
    }
    return render(request, 'academic_years_form.html', context)


def update_academic_year(request, year_id):
    page = "update"
    academic_year = get_object_or_404(AcademicYear, pk=year_id)
    if request.method == "POST":
        academic_year.closure = request.POST.get('closure')
        academic_year.finalClosure = request.POST.get('finalClosure')
        academic_year.save()
        return redirect('list_academic_years')
    context = {
        'page' : page,
        'academic_year': academic_year,
    }
    return render(request, 'academic_years_form.html', context)


def remove_academic_year(request, year_id):
    academic_year = get_object_or_404(AcademicYear, pk=year_id)
    academic_year.delete()
    return redirect('list_academic_years')




#faculty
def list_faculties(request):
    faculties = Faculties.objects.all()
    return render(request, 'list_faculties.html', {'faculties': faculties})


def create_faculty(request):
    page = "create"
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        Faculties.objects.create(name=name, description=description)
        return redirect('list_faculties')
    academic_years = AcademicYear.objects.all()
    context = {
        'page' : page,
        'academic_years': academic_years
    }
    return render(request, 'faculties_form.html', context)


def update_faculty(request, faculty_id):
    page = "update"
    faculty = get_object_or_404(Faculties, pk=faculty_id)
    if request.method == "POST":
        faculty.name = request.POST.get('name')
        faculty.description = request.POST.get('description')
        academicYear_id = request.POST.get('academicYear')
        faculty.academicYear = AcademicYear.objects.get(id=academicYear_id)
        faculty.save()
        return redirect('list_faculties')
    academic_years = AcademicYear.objects.all()
    context = {
        'page' : page,
        'faculty': faculty, 
        'academic_years': academic_years
    }
    return render(request, 'faculties_form.html', context)


def remove_faculty(request, faculty_id):
    faculty = get_object_or_404(Faculties, pk=faculty_id)
    faculty.delete()
    return redirect('list_faculties')


def create_role(request):
    if request.method == "POST":
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('role_list')  # giả sử bạn có một trang hiển thị danh sách các roles
    else:
        form = RoleForm()
    return render(request, 'create_role.html', {'form': form})

def role_list(request):
    roles = Role.objects.all()
    return render(request, 'role_list.html', {'roles': roles})

def delete_role(request, role_id):
    role = get_object_or_404(Role, id=role_id)
    role.delete()
    messages.success(request, 'The role has been successfully deleted!')
    return redirect('role_list') 


def all_contributions_view(request):
    contributions = Contributions.objects.all()  # Fetch all contributions from the database
    context = {
        'contributions': contributions
    }
    return render(request, 'manage_contributions.html', context)


def approve_contribution(request, contribution_id):
    contribution = get_object_or_404(Contributions, id=contribution_id)
    status = request.GET.get('approve')
    
    if request.method == "GET":
        if status == "app":  # Được thay đổi từ "Approve" thành "app" cho phù hợp với tham số URL
            contribution.status = True
        elif status == "dis":  # Được thay đổi từ "Disapprove" thành "dis" cho phù hợp
            contribution.status = False
        contribution.save()
        return redirect('manage_contributions')
    else:
        return redirect('home')  # Redirect if the method is not POST
    
#account:
def account_list(request):
    accounts = UserProfile.objects.all()
    return render(request, 'listAccount.html', {'accounts': accounts})

def account_update(request, pk):
    user_profile = get_object_or_404(UserProfile, pk=pk)

    if request.method == 'POST':
        user_profile.fullname = request.POST.get('fullname')
        user_profile.email = request.POST.get('email')
        user_profile.phone = request.POST.get('phone')

        faculty_id = request.POST.get('faculty')
        if faculty_id:
            user_profile.faculty = Faculties.objects.get(id=faculty_id)
        else:
            user_profile.faculty = None

        user_profile.save()

        selected_roles = request.POST.getlist('roles')
        user_profile.roles.clear()
        for role_id in selected_roles:
            role = Role.objects.get(id=role_id)
            user_profile.roles.add(role)

        return redirect('account_list')
    else:
        faculties = Faculties.objects.all()
        roles = Role.objects.all()
        return render(request, 'editAccount.html', {
            'user_profile': user_profile,
            'faculties': faculties,
            'roles': roles
        })

def account_delete(request, pk):
    if request.method == 'GET':
        account = get_object_or_404(UserProfile, pk=pk)
        account.delete()
        return redirect('account_list')
    
def statistical_analysis(request):
    total_contributions = Contributions.objects.count()
    approved_contributions = Contributions.objects.filter(status=True).count()

    contributions_by_faculty = Contributions.objects.values('faculty__name').annotate(total=Count('id'))
    approved_by_faculty = Contributions.objects.filter(status=True).values('faculty__name').annotate(total=Count('id'))

    faculty_names = [item['faculty__name'] for item in contributions_by_faculty]
    contributions_counts = [item['total'] for item in contributions_by_faculty]
    approved_counts = [item['total'] for item in approved_by_faculty]

    context = {
        'total_contributions': total_contributions,
        'approved_contributions': approved_contributions,
        'faculty_names': faculty_names,
        'contributions_by_faculty': contributions_counts,
        'approved_by_faculty': approved_counts,
    }
    return render(request, 'statistical_analysis.html', context)

def approve_contribution(request, contribution_id):
    contribution = get_object_or_404(Contributions, id=contribution_id)
    contribution.status ='approved'
    contribution.save()
    return redirect('manage_contributions')

@csrf_protect
def reject_contribution(request, contribution_id):
    if request.method == "POST":
        contribution = get_object_or_404(Contributions, id=contribution_id)
        reject_reason = request.POST.get("reject_reason")
        contribution.reject_reason = reject_reason
        contribution.status = 'rejected'
        contribution.save()
        return redirect('manage_contributions')
    else:
        return redirect('some_view')
