# urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profiles/', views.ShowAllProfilesView.as_view(), name='show_all_profiles'),  # Existing view
    path('profile/<int:pk>/', views.ShowProfilePageView.as_view(), name='show_profile'),
    path('create_profile/', views.CreateProfileView.as_view(), name='create_profile'),
    path('login/', auth_views.LoginView.as_view(template_name='tide/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/<int:pk>/update/', views.UpdateProfileView.as_view(), name='update_profile'),
    path('profile/<int:pk>/friend_suggestions/', views.ShowFriendSuggestionsView.as_view(), name='friend_suggestions'),
    path('profile/<int:pk>/add_friend/<int:other_pk>/', views.CreateFriendView.as_view(), name='add_friend'),
    path('profile/<int:pk>/remove_friend/<int:other_pk>/', views.RemoveFriendView.as_view(), name='remove_friend'),
    path('profile/<int:pk>/status/create/', views.CreateStatusMessageView.as_view(), name='create_status_message'),
    path('status/<int:pk>/update/', views.UpdateStatusMessageView.as_view(), name='update_status_message'),
    path('status/<int:pk>/delete/', views.DeleteStatusMessageView.as_view(), name='delete_status_message'),
    path('profile/<int:pk>/news_feed/', views.ShowNewsFeedView.as_view(), name='news_feed'),


]
