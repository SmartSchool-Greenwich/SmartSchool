from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import ContributionFiles, UserProfile, Faculties, Contributions, Role
from django.contrib.auth.decorators import login_required

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
    if request.method == 'POST':
        if request.POST['username'] and request.POST['fullname'] and request.POST['phone'] and request.POST['password'] and request.POST['repassword']:
            username =  request.POST['username']
            email = request.POST.get('email')
            fullname = request.POST.get('fullname')
            phone = request.POST.get('phone')
            password = request.POST.get('password')
            repassword = request.POST.get('repassword')

        if password == repassword:
            if User.objects.filter(username = username).exists():
                return redirect('register')
            else:
                user = User.objects.create_user(username=username,password=password,email=email)   
                user.save()
                
                userprofile = UserProfile(user=user, fullname=fullname, email=email, phone=phone)
                userprofile.save()
                return redirect('login')
        else:
            return redirect('register') 

    return render(request, 'register.html')

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
        phone = request.POST.get('phone', '')  # Giá trị mặc định là chuỗi rỗng nếu không có
        role_id = request.POST['role']

        if password == confirm_password:
            # Tạo user mới
            user = User.objects.create_user(username=username, password=password)
            
            # Tạo UserProfile mới và lưu ngay lập tức
            new_profile = UserProfile(user=user, fullname=fullname, phone=phone)
            new_profile.save()  # Lưu UserProfile để có thể thêm vào role

            # Thêm role vào UserProfile
            selected_role = Role.objects.get(id=role_id)  # Lấy role từ ID
            new_profile.roles.add(selected_role)  # Không cần gọi save() sau khi thêm role

            return redirect('login')  # Redirect to a login page after successful registration
        else:
            # Thêm logic xử lý lỗi nếu mật khẩu không khớp hoặc thông tin không đầy đủ
            pass  

    roles = Role.objects.all()  # Lấy tất cả roles cho dropdown
    return render(request, 'create_account.html', {'roles': roles})


def faculty_files(request, faculty_id):
    faculty = get_object_or_404(Faculties, pk=faculty_id)
    contributions = Contributions.objects.filter(faculty=faculty)
    files = ContributionFiles.objects.filter(contribution__in=contributions).distinct()
    
    return render(request, 'faculty_file.html', {'faculty': faculty, 'files': files})