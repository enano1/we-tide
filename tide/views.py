from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from .models import Profile, StatusMessage, Image
from .forms import CreateProfileForm, UpdateProfileForm, CreateStatusMessageForm, LocationForm
import requests
from decouple import config

class ShowAllProfilesView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = 'tide/show_all_profiles.html'
    context_object_name = 'profiles'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['has_profile'] = Profile.objects.filter(user=self.request.user).exists()
        return context
    
class ShowProfilePageView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'tide/show_profile.html'  
    context_object_name = 'profile'
    login_url = '/login/'

class CreateProfileView(CreateView):
    model = Profile
    form_class = CreateProfileForm
    template_name = 'tide/create_profile.html'

    def form_valid(self, form):
        self.object = form.save()
        return redirect('show_profile', pk=self.object.pk)

class UpdateProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = UpdateProfileForm
    template_name = 'tide/update_profile_form.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, pk=self.kwargs['pk'], user=self.request.user)

    def get_success_url(self):
        return reverse('show_profile', kwargs={'pk': self.object.pk})

class CreateFriendView(LoginRequiredMixin, View):
    def post(self, request, pk, other_pk):
        profile = get_object_or_404(Profile, pk=pk)
        other_profile = get_object_or_404(Profile, pk=other_pk)
        
        profile.add_friend(other_profile)
        messages.success(request, f'You are now friends with {other_profile.fname} {other_profile.lname}!')
        
        return redirect('show_profile', pk=profile.pk)

class ShowFriendSuggestionsView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'tide/friend_suggestions.html'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['friend_suggestions'] = self.object.get_friend_suggestions()
        return context

class RemoveFriendView(LoginRequiredMixin, View):
    def post(self, request, pk, other_pk):
        profile = get_object_or_404(Profile, pk=pk)
        other_profile = get_object_or_404(Profile, pk=other_pk)

        profile.remove_friend(other_profile)
        messages.success(request, f'You are no longer friends with {other_profile.fname} {other_profile.lname}.')
        return redirect('show_profile', pk=profile.pk)

class CreateStatusMessageView(LoginRequiredMixin, CreateView):
    form_class = CreateStatusMessageForm
    template_name = 'tide/create_status_form.html'

    def get_login_url(self) -> str:
        return reverse('login')

    def form_valid(self, form):
        sm = form.save(commit=False)
        profile = Profile.objects.get(pk=self.kwargs['pk'])
        sm.profile = profile
        sm.save()

        image_file = form.cleaned_data.get('image_file')
        if image_file:
            image = Image(image_file=image_file, status_message=sm)
            image.save()

        return redirect('show_profile', pk=profile.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = Profile.objects.get(pk=self.kwargs['pk'])
        context['profile'] = profile
        return context

    def get_success_url(self):
        return reverse('show_profile', args=[self.kwargs['pk']])

class DeleteStatusMessageView(LoginRequiredMixin, DeleteView):
    model = StatusMessage
    template_name = 'tide/delete_status_form.html'
    context_object_name = 'status_message'

    def get_login_url(self) -> str:
        return reverse('login')

    def get_success_url(self):
        profile_pk = self.object.profile.pk  
        return reverse('show_profile', args=[profile_pk])

class UpdateStatusMessageView(LoginRequiredMixin, UpdateView):
    model = StatusMessage
    fields = ['message']  
    template_name = 'tide/update_status_form.html'
    context_object_name = 'status_message'

    def get_login_url(self) -> str:
        return reverse('login')

    def get_success_url(self):
        profile_pk = self.object.profile.pk  
        return reverse('show_profile', args=[profile_pk])

class ShowNewsFeedView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'tide/news_feed.html'
    context_object_name = 'profile'

    def get_login_url(self) -> str:
        return reverse('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['news_feed'] = self.object.get_news_feed()
        return context


### DASHBOARD VIEW ###

class DashboardView(View):
    template_name = 'tide/dashboard.html'

    def get(self, request, *args, **kwargs):
        context = {
            'welcome_message': "Welcome to your dashboard",
        }
        return render(request, self.template_name, context)

# def get_tide_data(request):
#     if request.method == "POST":
#         form = LocationForm(request.POST)
#         if form.is_valid():
#             station_id = form.cleaned_data['station_id']
#             # Redirect to results page with station_id
#             return redirect('tide_results', station_id=station_id)
#     else:
#         form = LocationForm()
#     return render(request, 'tide/location_input.html', {'form': form})

# def tide_results(request, station_id):
#     url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
#     params = {
#         "station": station_id,
#         "product": "water_level",
#         "datum": "MLLW",
#         "time_zone": "gmt",
#         "units": "metric",
#         "date": "today",
#         "application": "SurfApp",
#         "format": "json",
#     }

#     response = requests.get(url, params=params)
#     data = response.json()
#     return render(request, 'tide/tide_results.html', {'data': data, 'station_id': station_id})

import requests
from datetime import datetime, timedelta
import math


def tide_data_view(request, station_id):
    # Get the date from user input or default to today
    input_date = request.GET.get('date', datetime.today().strftime('%Y-%m-%d'))
    input_date_obj = datetime.strptime(input_date, '%Y-%m-%d')

    # Calculate days difference between today and input date
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    days_ahead = (input_date_obj - today).days

    # NOAA API for actual data on the chosen date
    formatted_date = input_date_obj.strftime('%Y%m%d')
    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        "begin_date": formatted_date,
        "end_date": formatted_date,
        "station": station_id,
        "product": "water_level",
        "datum": "MLLW",
        "time_zone": "gmt",
        "units": "metric",
        "application": "your_app_name",
        "format": "json",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if 'data' in data:
            tide_data = [
                record for record in data['data']
                if record['v'] and record['v'].strip()  # Filter out empty values
            ]

            time_shift = timedelta(minutes=50 * days_ahead)
            adjusted_data = [
                {
                    't': (datetime.strptime(record['t'], '%Y-%m-%d %H:%M') + time_shift).strftime('%H:%M'),
                    'v': record['v']
                }
                for record in tide_data
            ]

            label = "Predicted" if days_ahead > 0 else "Actual"
            is_predicted = days_ahead > 0

            # Get valid max/min tide after filtering
            max_tide = max(adjusted_data, key=lambda x: float(x['v']))
            min_tide = min(adjusted_data, key=lambda x: float(x['v']))
            optimal_times = [record for record in adjusted_data if 0.5 <= float(record['v']) <= 1.5]

            chart_labels = [record['t'] for record in adjusted_data]
            chart_values = [float(record['v']) for record in adjusted_data]
        else:
            adjusted_data = []
            max_tide = min_tide = None
            optimal_times = []
            chart_labels = chart_values = []
            label = "No Data"
            is_predicted = False

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        adjusted_data = []
        max_tide = min_tide = None
        optimal_times = []
        chart_labels = chart_values = []
        label = "Error"
        is_predicted = False

    return render(request, 'tide/tide_data.html', {
        'data': adjusted_data,
        'station_id': station_id,
        'max_tide': max_tide,
        'min_tide': min_tide,
        'optimal_times': optimal_times,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'label': label,
        'is_predicted': is_predicted,
        'selected_date': input_date,  # Pass selected date
    })

from django.shortcuts import render, redirect
from math import radians, sin, cos, sqrt, atan2

# Mock NOAA Stations for Demo
NOAA_STATIONS = [
    {'id': '9414290', 'name': 'San Francisco, CA', 'lat': 37.7749, 'lng': -122.4194},
    {'id': '9410230', 'name': 'Los Angeles, CA', 'lat': 34.0522, 'lng': -118.2437},
    {'id': '9432780', 'name': 'Seattle, WA', 'lat': 47.6062, 'lng': -122.3321},
    {'id': '9410170', 'name': 'San Diego, CA', 'lat': 32.7157, 'lng': -117.1611},
    {'id': '8418150', 'name': 'Boston, MA', 'lat': 42.3601, 'lng': -71.0589},
    {'id': '8723214', 'name': 'Miami, FL', 'lat': 25.7617, 'lng': -80.1918},
    {'id': '8658120', 'name': 'Charleston, SC', 'lat': 32.7765, 'lng': -79.9311},
    {'id': '8638610', 'name': 'Norfolk, VA', 'lat': 36.8508, 'lng': -76.2859},
    {'id': '8775241', 'name': 'Galveston, TX', 'lat': 29.3013, 'lng': -94.7977},
    {'id': '8747437', 'name': 'New Orleans, LA', 'lat': 29.9511, 'lng': -90.0715},
    {'id': '8761927', 'name': 'Houston, TX', 'lat': 29.7604, 'lng': -95.3698},
    {'id': '9410660', 'name': 'Santa Barbara, CA', 'lat': 34.4208, 'lng': -119.6982},
    {'id': '9416841', 'name': 'Oakland, CA', 'lat': 37.8044, 'lng': -122.2711},
    {'id': '8516945', 'name': 'New York, NY', 'lat': 40.7128, 'lng': -74.0060},
    {'id': '8443970', 'name': 'Portland, ME', 'lat': 43.6591, 'lng': -70.2568},
    {'id': '9461380', 'name': 'Anchorage, AK', 'lat': 61.2181, 'lng': -149.9003},
    {'id': '9468756', 'name': 'Juneau, AK', 'lat': 58.3019, 'lng': -134.4197},
    {'id': '1612340', 'name': 'Honolulu, HI', 'lat': 21.3069, 'lng': -157.8583},
    {'id': '1617760', 'name': 'Kailua-Kona, HI', 'lat': 19.6399, 'lng': -155.9969},
]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def dashboard_view(request):
    return render(request, 'dashboard.html', {'welcome_message': 'Welcome to your Dashboard!'})

def location_input_view(request):
    if request.method == 'POST':
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return render(request, 'tide/location_input.html', {
                'error': 'Please enter valid latitude and longitude as decimals.'
            })

        return redirect('nearest_station', latitude=latitude, longitude=longitude)

    return render(request, 'tide/location_input.html')

def nearest_station_view(request, latitude, longitude):
    latitude = float(latitude)
    longitude = float(longitude)
    closest_station = min(NOAA_STATIONS, key=lambda station: haversine(latitude, longitude, station['lat'], station['lng']))
    return render(request, 'tide/nearest_station.html', {'station': closest_station})


def weather_view(request, lat, lon):
    api_key = config('OPENWEATHER_API_KEY')
    weather_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'units': 'metric'
    }

    weather_data = {}
    try:
        response = requests.get(weather_url, params=params)
        response.raise_for_status()
        weather_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")

    return render(request, 'tide/weather.html', {
        'weather_data': weather_data,
        'lat': lat,
        'lon': lon,
        'api_key': api_key,  # Pass the API key for map
    })
