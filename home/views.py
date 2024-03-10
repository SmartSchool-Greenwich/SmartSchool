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
    faculties = Faculties.objects.all()
    can_upload = False 
    
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
            faculty = user_profile.faculty
            academic_year = faculty.academicYear if faculty else None
            if academic_year and timezone.now() < academic_year.closure:
                can_upload = True
        except UserProfile.DoesNotExist:
            can_upload = False
    
    context = {
        'faculties': faculties,
        'can_upload': can_upload,
    }
    return render(request, 'home.html', context)

def file_upload_view(request):
    faculties = Faculties.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        faculty_id = request.POST.get('faculty')
        term = request.POST.get('term') == 'on'
        
        try:
            faculty = Faculties.objects.get(id=faculty_id)
            contribution = Contributions.objects.create(
                title=title,
                content=content,
                faculty=faculty,
                term=term
            )
            contribution.user.add(request.user.userprofile)
            
            contribution_file = ContributionFiles(contribution=contribution)  
            for file in request.FILES.getlist('word') + request.FILES.getlist('img'):
                if file.name.endswith('.doc') or file.name.endswith('.docx'):
                    contribution_file.word = file
                else:
                    contribution_file.img = file
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
        context = {'faculties': faculties}
        
    return render(request, 'upload.html', context)

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
    faculty = get_object_or_404(Faculties, pk=faculty_id)
    contributions = Contributions.objects.filter(faculty=faculty)
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
    return render(request, 'faculty_file.html', {'faculty': faculty, 'files': files})

def show_contributions(request):
    contributions = Contributions.objects.all()
    
    return render(request, 'show_contribution.html', {'contributions': contributions})


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
    if request.method == 'POST':
        user_profile.fullname = request.POST.get('fullname', '')
        user_profile.email = request.POST.get('email', '')
        user_profile.phone = request.POST.get('phone', '')
        user_profile.save()
        return redirect('home')
    else:
        return render(request, 'update_profile.html', {'user_profile': user_profile})

def contributions_detail(request, contribution_id):
    contribution = get_object_or_404(Contributions, id=contribution_id)
    comments = Comment.objects.filter(contribution=contribution)
    can_update = False 
    
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
            faculty = user_profile.faculty
            academic_year = faculty.academicYear if faculty else None
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
    })    



def my_contributions(request):
    user_profile = UserProfile.objects.get(user=request.user)
    contributions = Contributions.objects.filter(user=user_profile).prefetch_related('faculty', 'files')
    can_upload = False 
    can_update = False 
    
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
            faculty = user_profile.faculty
            academic_year = faculty.academicYear if faculty else None
            if academic_year and timezone.now() < academic_year.closure:
                can_upload = True
            if academic_year and timezone.now() < academic_year.finalClosure:
                can_update = True
        except UserProfile.DoesNotExist:
            can_upload = False
            can_update = False 

    
    context = {
        'can_upload': can_upload,
        'can_update': can_update,
        'contributions': contributions
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
    return render(request, 'profile.html', {'user_profile': user_profile})





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
    faculties = Faculties.objects.all().select_related('academicYear')
    return render(request, 'list_faculties.html', {'faculties': faculties})


def create_faculty(request):
    page = "create"
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        academicYear_id = request.POST.get('academicYear')
        academicYear = AcademicYear.objects.get(id=academicYear_id)
        Faculties.objects.create(name=name, description=description, academicYear=academicYear)
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
        # Cập nhật thông tin cơ bản
        user_profile.fullname = request.POST.get('fullname')
        user_profile.email = request.POST.get('email')
        user_profile.phone = request.POST.get('phone')

        # Cập nhật faculty
        faculty_id = request.POST.get('faculty')
        if faculty_id:
            user_profile.faculty = Faculties.objects.get(id=faculty_id)
        else:
            user_profile.faculty = None

        user_profile.save()

        # Cập nhật roles
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
    if request.method == 'POST':
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


def admin(request):
    faculties = Faculties.objects.all()
    can_upload = False 
    
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
            faculty = user_profile.faculty
            academic_year = faculty.academicYear if faculty else None
            if academic_year and timezone.now() < academic_year.closure:
                can_upload = True
        except UserProfile.DoesNotExist:
            can_upload = False
    
    context = {
        'faculties': faculties,
        'can_upload': can_upload,
    }
    return render(request, 'ad_index.html', context)