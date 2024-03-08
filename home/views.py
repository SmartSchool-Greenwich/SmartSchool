from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import ContributionFiles, UserProfile, Faculties, Contributions, Role,AcademicYear, Comment
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from .forms import CommentForm, FileForm
from django.urls import reverse
import zipfile
from io import BytesIO

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
    context = { 
        'faculties':faculties
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
            
            # Vòng lặp xử lý mỗi file được upload
            contribution_file = ContributionFiles(contribution=contribution)  # Tạo đối tượng mới cho mỗi file
            for file in request.FILES.getlist('word') + request.FILES.getlist('img'):
                if file.name.endswith('.doc') or file.name.endswith('.docx'):
                    contribution_file.word = file
                else:
                    contribution_file.img = file
                contribution_file.save()

            return redirect('success_url') 
        except Faculties.DoesNotExist:
            return redirect('home')
        except Exception as e:
            print(e)  # Ghi rõ lỗi ra để dễ dàng gỡ rối
            return redirect('home')
    
    else:
        context = {'faculties': faculties}
        
    return render(request, 'upload.html', context)


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
        faculty_id = request.POST.get('faculty', None)  # Lấy faculty nếu có

        if password == confirm_password:
            # Tạo user mới
            user = User.objects.create_user(username=username, password=password)

            # Tạo UserProfile mới
            new_profile = UserProfile(user=user, fullname=fullname, phone=phone)

            # Kiểm tra và thêm faculty nếu role tương ứng và faculty_id được cung cấp
            if faculty_id:
                try:
                    faculty = Faculties.objects.get(id=faculty_id)
                    new_profile.faculty = faculty
                except Faculties.DoesNotExist:
                    # Xử lý trường hợp không tìm thấy faculty
                    pass  # Hoặc bạn có thể thêm logic xử lý lỗi ở đây

            # Lưu UserProfile
            new_profile.save()

            # Thêm role vào UserProfile
            selected_role = Role.objects.get(id=role_id)
            new_profile.roles.add(selected_role)

            return redirect('login')
    else:  # GET request
        roles = Role.objects.all()
        faculties = Faculties.objects.all()  # Giả sử bạn muốn hiển thị tất cả faculties trong form
        return render(request, 'create_account.html', {'roles': roles, 'faculties': faculties})


def create_faculty(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        closure = parse_datetime(request.POST.get('closure'))
        finalClosure = parse_datetime(request.POST.get('finalClosure'))

        if name and closure and finalClosure:
            faculty = Faculties.objects.create(name=name)
            AcademicYear.objects.create(faculties=faculty, closure=closure, finalClosure=finalClosure)
            return redirect('home') 
         # Điều hướng đến URL danh sách Faculties sau khi tạo
    return render(request, 'faculty_create.html')

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
            # Sử dụng UserProfile thay vì User
                user_profile, created = UserProfile.objects.get_or_create(user=request.user)
                new_comment.user = user_profile
                new_comment.save()
                return redirect('faculty_files', faculty_id=faculty_id)
            except Contributions.DoesNotExist:
                return HttpResponse("Contribution does not exist", status=404)
    return render(request, 'faculty_file.html', {'faculty': faculty, 'files': files})

def show_contributions(request):
    # Lấy tất cả contributions từ database
    contributions = Contributions.objects.all()
    
    # Render template, truyền 'contributions' vào context để có thể sử dụng trong template
    return render(request, 'show_contribution.html', {'contributions': contributions})


#download file zip
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
        # Update user profile information from the form
        user_profile.fullname = request.POST.get('fullname', '')
        user_profile.email = request.POST.get('email', '')
        user_profile.phone = request.POST.get('phone', '')
        user_profile.save()
        return redirect('home')
    else:
        # Pass existing user profile information to the template
        return render(request, 'update_profile.html', {'user_profile': user_profile})

def contributions_detail(request, contribution_id):
    contribution = get_object_or_404(Contributions, id=contribution_id)
    comments = Comment.objects.filter(contribution=contribution)

    if request.method == "POST":
        # Xử lý thêm comment
        if 'comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                new_comment = comment_form.save(commit=False)
                new_comment.contribution = contribution
                # Giả sử UserProfile được liên kết với User qua một trường `user`
                new_comment.user = request.user.userprofile
                new_comment.save()
                return HttpResponseRedirect(reverse('contribution_detail', args=[contribution_id]))

        # Xử lý upload file mới
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
        'file_form': file_form
    })    
