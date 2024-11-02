# urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.ShowAllProfilesView.as_view(), name='show_all_profiles'),  
    path('profile/<int:pk>/', views.ShowProfilePageView.as_view(), name='show_profile'),
    path('create_profile/', views.CreateProfileView.as_view(), name='create_profile'),
    path('login/', auth_views.LoginView.as_view(template_name='tide/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
