# urls.py
from django.urls import path, register_converter
from django.contrib.auth import views as auth_views
from . import views

class FloatConverter:
    regex = r'-?\d+\.\d+'

    def to_python(self, value):
        return float(value)

    def to_url(self, value):
        return str(value)

register_converter(FloatConverter, 'float')

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    # path('profiles/', views.ShowAllProfilesView.as_view(), name='show_all_profiles'),  # Existing view
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
    path('tide-data/<str:station_id>/', views.tide_data_view, name='tide_data'),
    path('location/', views.location_input_view, name='location_input'),
    path('nearest-station/<float:latitude>/<float:longitude>/', views.nearest_station_view, name='nearest_station'),
    path('weather/<float:lat>/<float:lon>/', views.weather_view, name='weather_view'),
    path('tide-info/', views.tide_info_view, name='tide_info'),
    path('save_station/', views.SaveStationView.as_view(), name='save_station'),
    path('saved-locations/', views.SavedLocationsView.as_view(), name='saved_locations'),
    path('all_friends/', views.AllFriendsView.as_view(), name='all_friends'),
    path('surf_sessions/', views.SurfSessionListView.as_view(), name='surf_sessions'),
    path('surf_sessions/new/', views.CreateSurfSessionView.as_view(), name='create_surf_session'),
    path('surf_sessions/<int:pk>/update/', views.UpdateSurfSessionView.as_view(), name='update_surf_session'),
    path('surf_sessions/<int:pk>/delete/', views.DeleteSurfSessionView.as_view(), name='delete_surf_session'),



]
