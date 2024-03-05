from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    path('upload/', views.file_upload_view, name='file_upload'),
    path('upload/success/', views.upload_success, name='success_url'),
    path('create_account/', views.craete_account, name='create_account'),
    path('faculties/<int:faculty_id>/files/', views.faculty_files, name='faculty_files'),
]