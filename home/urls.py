from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),
    path('upload/', views.file_upload_view, name='file_upload'),
    path('upload/success/', views.upload_success, name='success_url'),
    path('create_account/', views.create_account, name='create_account'),
    path('faculties/<int:faculty_id>/files/', views.faculty_files, name='faculty_files'),
    path('create_faculties/', views.create_faculty, name='faculty-add'),
    path('show-contributions/', views.show_contributions, name='show_contributions'),
    path('download/contributions/', views.download_selected_contributions, name='download_selected_contributions'),
    path('update_profile/', views.update_profile, name='update_profile'),

]