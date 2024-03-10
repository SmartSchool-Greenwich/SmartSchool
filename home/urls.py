from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),
    path('upload/', views.file_upload_view, name='file_upload'),
    path('contribution/update/<int:pk>/', views.update_contribution, name='update_contribution'),
    path('contribution/delete/<int:pk>/', views.delete_contribution, name='delete_contribution'),
    path('upload/success/', views.upload_success, name='success_url'),
    path('create_account/', views.create_account, name='create_account'),
    path('faculties/<int:faculty_id>/files/', views.faculty_files, name='faculty_files'),
    path('show-contributions/', views.show_contributions, name='show_contributions'),
    path('download/contributions/', views.download_selected_contributions, name='download_selected_contributions'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('contributions/<int:contribution_id>/', views.contributions_detail, name='contributions_detail'),
    path('my-contributions/', views.my_contributions, name='my_contributions'),

    path('update-faculties/<int:faculty_id>/', views.update_faculty, name='update_faculty'),
    path('remove-faculties/<int:faculty_id>/', views.remove_faculty, name='remove_faculty'),
    path('profile/', views.user_profile, name='profile'),


    path('academic-years/', views.list_academic_years, name='list_academic_years'),
    path('academic-years/create/', views.create_academic_year, name='create_academic_year'),
    path('academic-years/update/<int:year_id>/', views.update_academic_year, name='update_academic_year'),
    path('academic-years/remove/<int:year_id>/', views.remove_academic_year, name='remove_academic_year'),


    path('faculties/', views.list_faculties, name='list_faculties'),
    path('faculties/create/', views.create_faculty, name='create_faculty'),
    path('faculties/update/<int:faculty_id>/', views.update_faculty, name='update_faculty'),
    path('faculties/remove/<int:faculty_id>/', views.remove_faculty, name='remove_faculty'),

    path('create_role/', views.create_role, name='create_role'),
    path('role_list/', views.role_list, name='role_list'),

    path('manage_contributions/', views.all_contributions_view, name='manage_contributions'),
    path('contributions/approve/<int:contribution_id>/', views.approve_contribution, name='approve_contribution'),

]