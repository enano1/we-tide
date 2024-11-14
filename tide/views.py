from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from .models import Profile, StatusMessage, Image, SurfSpot, SurfSession, Comment
from .forms import CreateProfileForm, UpdateProfileForm, CreateStatusMessageForm, LocationForm, SurfSessionForm, CommentForm
import requests
from decouple import config
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from django.utils.timezone import make_aware, now, is_naive


class ShowAllProfilesView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = 'tide/show_all_profiles.html'
    context_object_name = 'profiles'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['has_profile'] = Profile.objects.filter(user=self.request.user).exists()
        return context

class AllFriendsView(LoginRequiredMixin, View):
    def get(self, request):
        profile = request.user.profile  
        friends = profile.get_friends()  
        return render(request, 'tide/all_friends.html', {'profile': profile, 'friends': friends})
    
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
        profile = Profile.objects.get(pk=self.kwargs['pk'])
        sm = form.save(commit=False)
        sm.profile = profile
        sm.save()

        # Save associated image if provided
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

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

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'tide/dashboard.html'
    welcome_message = 'Welcome to your Dashboard!'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['welcome_message'] = self.welcome_message
        context['surf_spots'] = SurfSpot.objects.filter(user=self.request.user)
        context['recent_surf_sessions'] = SurfSession.objects.filter(user=self.request.user).order_by('-date')[:5]  

        return context



def tide_data_view(request, station_id):
    input_date = request.GET.get('date', datetime.today().strftime('%Y-%m-%d'))
    input_date_obj = datetime.strptime(input_date, '%Y-%m-%d')

    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    days_ahead = (input_date_obj - today).days

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
                if record['v'] and record['v'].strip() 
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
        'selected_date': input_date,  
    })


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # earth's radius in km!
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def location_input_view(request):
    if request.method == 'POST':
        address = request.POST.get('address')

        if not address:
            return render(request, 'tide/location_input.html', {
                'error': 'Please enter a valid address.'
            })

        api_key = config('GOOGLE_API_KEY')  
        geocode_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'
        
        response = requests.get(geocode_url)
        data = response.json()

        if data['status'] == 'OK':
            latitude = data['results'][0]['geometry']['location']['lat']
            longitude = data['results'][0]['geometry']['location']['lng']
            
            return redirect('nearest_station', latitude=latitude, longitude=longitude)
        else:
            return render(request, 'tide/location_input.html', {
                'error': 'Unable to find the location. Please try again with a different address.'
            })

    return render(request, 'tide/location_input.html')


def nearest_station_view(request, latitude, longitude):
    """
    This view takes a latitude and longitude from the URL and finds the closest
    NOAA tide station. It renders a template with the station name, id,
    latitude, longitude, and a link to view the tide data for that station.
    """
    latitude = float(latitude)
    longitude = float(longitude)
    closest_station = min(NOAA_STATIONS, key=lambda station: haversine(latitude, longitude, station['lat'], station['lng']))
    return render(request, 'tide/nearest_station.html', {'station': closest_station})


def get_moon_phase(date):
    if is_naive(date):  
        date = make_aware(date)

    base_date = make_aware(datetime(2000, 1, 6))
    diff = (date - base_date).days
    lunations = 29.53058867  # the average length of the lunar cycle in days
    phase_index = (diff % lunations) / lunations

    if phase_index < 0.03 or phase_index > 0.97:
        phase_name = "New Moon"
        phase_description = "Spring tides are strongest around this phase, with high highs and low lows."
    elif 0.22 < phase_index < 0.28:
        phase_name = "First Quarter"
        phase_description = "Neap tides occur with moderate tidal ranges."
    elif 0.47 < phase_index < 0.53:
        phase_name = "Full Moon"
        phase_description = "Spring tides occur again, creating stronger tidal effects."
    elif 0.72 < phase_index < 0.78:
        phase_name = "Last Quarter"
        phase_description = "Neap tides occur again with more moderate tidal ranges."
    else:
        phase_name = "Waxing or Waning Phase"
        phase_description = "Tidal ranges are gradually changing."
    print(phase_index)

    return {'phase_name': phase_name, 'phase_description': phase_description}

def weather_view(request, lat, lon):
    api_key = config('OPENWEATHER_API_KEY')
    weather_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
        'units': 'imperial'
    }

    weather_data = {}
    try:
        response = requests.get(weather_url, params=params)
        response.raise_for_status()
        weather_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")

    current_date = now()  
    moon_phase = get_moon_phase(current_date)

    return render(request, 'tide/weather.html', {
        'weather_data': weather_data,
        'lat': lat,
        'lon': lon,
        'api_key': api_key,
        'moon_phase': moon_phase  
    })


def tide_info_view(request):
    return render(request, 'tide/tide_info.html')


class SaveStationView(LoginRequiredMixin, View):
    def post(self, request):
        station_id = request.POST.get("station_id")
        name = request.POST.get("name")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        nickname = request.POST.get("nickname", "")

        # to check if this station is already saved
        if SurfSpot.objects.filter(user=request.user, station_id=station_id).exists():
            messages.info(request, "Station already saved.")
        else:
            SurfSpot.objects.create(
                user=request.user,
                station_id=station_id,
                nickname=nickname,
                latitude=latitude,
                longitude=longitude,
            )
            messages.success(request, "Station saved successfully!")

        return redirect('dashboard')

class SavedLocationsView(LoginRequiredMixin, View):
    def get(self, request):
        surf_spots = SurfSpot.objects.filter(user=request.user)
        return render(request, 'tide/saved_locations.html', {'surf_spots': surf_spots})

class CreateSurfSessionView(CreateView):
    model = SurfSession
    form_class = SurfSessionForm
    template_name = 'tide/create_surf_session.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class SurfSessionListView(LoginRequiredMixin, ListView):
    model = SurfSession
    template_name = 'tide/surf_sessions.html'
    context_object_name = 'surf_sessions'

    def get_queryset(self):
        return SurfSession.objects.filter(user=self.request.user).order_by('-date')
    


class ViewSurfSessionView(LoginRequiredMixin, DetailView):
    model = SurfSession
    template_name = 'tide/view_surf_session.html'
    context_object_name = 'surf_session'


class UpdateSurfSessionView(LoginRequiredMixin, UpdateView):
    model = SurfSession
    form_class = SurfSessionForm
    template_name = 'tide/update_surf_session_form.html'

    def get_object(self, queryset=None):
        return get_object_or_404(SurfSession, pk=self.kwargs['pk'], user=self.request.user)

    def get_success_url(self):
        return reverse('surf_sessions')

class DeleteSurfSessionView(LoginRequiredMixin, DeleteView):
    model = SurfSession
    template_name = 'tide/delete_surf_session_form.html'
    context_object_name = 'surf_session'

    def get_object(self, queryset=None):
        return get_object_or_404(SurfSession, pk=self.kwargs['pk'], user=self.request.user)

    def get_success_url(self):
        return reverse('surf_sessions')
    
class CreateCommentView(CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'tide/create_comment.html'

    def form_valid(self, form):
        comment = form.save(commit=False)

        if 'status_message_id' in self.kwargs:
            comment.status_message = get_object_or_404(StatusMessage, pk=self.kwargs['status_message_id'])
        elif 'parent_comment_id' in self.kwargs:
            parent_comment = get_object_or_404(Comment, pk=self.kwargs['parent_comment_id'])
            comment.parent_comment = parent_comment
            comment.status_message = parent_comment.status_message
        
        comment.profile = self.request.user.profile
        comment.save()

        if 'news_feed' in self.request.POST:
            return redirect('news_feed', pk=comment.status_message.profile.id)
        else:
            return redirect('show_profile', pk=comment.status_message.profile.id)


class DeleteCommentView(DeleteView):
    model = Comment
    template_name = 'tide/confirm_delete.html'  

    def get_success_url(self):
        if 'news_feed' in self.request.POST:
            return reverse_lazy('news_feed', kwargs={'pk': self.object.status_message.profile.id})
        else:
            return reverse_lazy('show_profile', kwargs={'pk': self.object.status_message.profile.id if self.object.status_message else self.object.parent_comment.profile.id})

class SurfSessionPublicListView(ListView):
    model = SurfSession
    template_name = 'tide/surf_sessions_public.html'
    context_object_name = 'surf_sessions'

    def get_queryset(self):
        queryset = SurfSession.objects.all().order_by('-date')

        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        surf_spot = self.request.GET.get('surf_spot')
        wave_rating = self.request.GET.get('wave_rating')

        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if surf_spot:
            queryset = queryset.filter(surf_spot__id=surf_spot)
        if wave_rating:
            queryset = queryset.filter(wave_rating=wave_rating)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['surf_spots'] = SurfSpot.objects.all()
        return context


############################################################################
############################ NOAA STATIONS DATA ############################
############################################################################

##parsed this data from noaa xml dataset
NOAA_STATIONS = [
    {'id': '1611400', 'name': 'Nawiliwili', 'lat': 21.9544, 'lng': -159.3561},
    {'id': '1612340', 'name': 'Honolulu', 'lat': 21.3033, 'lng': -157.8645},
    {'id': '1612401', 'name': 'Pearl Harbor', 'lat': 21.3675, 'lng': -157.9639},
    {'id': '1612480', 'name': 'Mokuoloe', 'lat': 21.4331, 'lng': -157.79},
    {'id': '1615680', 'name': 'Kahului, Kahului Harbor', 'lat': 20.895, 'lng': -156.4692},
    {'id': '1617433', 'name': 'Kawaihae', 'lat': 20.0366, 'lng': -155.8294},
    {'id': '1617760', 'name': 'Hilo, Hilo Bay, Kuhio Bay', 'lat': 19.7303, 'lng': -155.06},
    {'id': '1619910', 'name': 'Sand Island, Midway Islands', 'lat': 28.2117, 'lng': -177.36},
    {'id': '1630000', 'name': 'Apra Harbor, Guam', 'lat': 13.4434, 'lng': 144.6564},
    {'id': '1631428', 'name': 'Pago Bay, Guam', 'lat': 13.4283, 'lng': 144.7989},
    {'id': '1770000', 'name': 'Pago Pago, American Samoa', 'lat': -14.28, 'lng': -170.69},
    {'id': '1820000', 'name': 'Kwajalein, Marshall Islands', 'lat': 8.7317, 'lng': 167.7361},
    {'id': '1890000', 'name': 'Wake Island, Pacific Ocean', 'lat': 19.2906, 'lng': 166.6175},
    {'id': '2695535', 'name': 'Bermuda Biological Station', 'lat': 32.37, 'lng': -64.695},
    {'id': '2695540', 'name': 'Bermuda, St. Georges Island', 'lat': 32.3733, 'lng': -64.7033},
    {'id': '8311030', 'name': 'Ogdensburg', 'lat': 44.7028, 'lng': -75.4944},
    {'id': '8311062', 'name': 'Alexandria Bay', 'lat': 44.3311, 'lng': -75.9345},
    {'id': '8410140', 'name': 'Eastport', 'lat': 44.9046, 'lng': -66.9829},
    {'id': '8411060', 'name': 'Cutler Farris Wharf', 'lat': 44.6567, 'lng': -67.21},
    {'id': '8413320', 'name': 'Bar Harbor', 'lat': 44.3922, 'lng': -68.2043},
    {'id': '8418150', 'name': 'Portland', 'lat': 43.6581, 'lng': -70.2442},
    {'id': '8419870', 'name': 'Seavey Island', 'lat': 43.0797, 'lng': -70.741},
    {'id': '8443970', 'name': 'Boston', 'lat': 42.3539, 'lng': -71.0503},
    {'id': '8447386', 'name': 'Fall River', 'lat': 41.7043, 'lng': -71.1641},
    {'id': '8447387', 'name': 'Borden Flats Light at Fall River', 'lat': 41.705, 'lng': -71.1733},
    {'id': '8447412', 'name': 'Fall River Visibility', 'lat': 41.6958, 'lng': -71.1798},
    {'id': '8447435', 'name': 'Chatham', 'lat': 41.6885, 'lng': -69.9511},
    {'id': '8447627', 'name': 'New Bedford, Barrier Gate', 'lat': 41.6244, 'lng': -70.9056},
    {'id': '8447636', 'name': 'New Bedford Harbor', 'lat': 41.6211, 'lng': -70.9136},
    {'id': '8447930', 'name': 'Woods Hole', 'lat': 41.5236, 'lng': -70.6711},
    {'id': '8449130', 'name': 'Nantucket Island', 'lat': 41.285, 'lng': -70.0967},
    {'id': '8452314', 'name': 'Sandy Point Visibility, Prudence Island', 'lat': 41.6051, 'lng': -71.3042},
    {'id': '8452660', 'name': 'Newport', 'lat': 41.5043, 'lng': -71.3261},
    {'id': '8452944', 'name': 'Conimicut Light', 'lat': 41.7171, 'lng': -71.3452},
    {'id': '8452951', 'name': 'Potter Cove, Prudence Island', 'lat': 41.6372, 'lng': -71.3393},
    {'id': '8453662', 'name': 'Providence Visibility', 'lat': 41.7857, 'lng': -71.3831},
    {'id': '8454000', 'name': 'Providence', 'lat': 41.8072, 'lng': -71.4007},
    {'id': '8454049', 'name': 'Quonset Point', 'lat': 41.5869, 'lng': -71.41},
    {'id': '8454123', 'name': 'Port of Davisville', 'lat': 41.6112, 'lng': -71.4103},
    {'id': '8461490', 'name': 'New London', 'lat': 41.3717, 'lng': -72.0956},
    {'id': '8465705', 'name': 'New Haven', 'lat': 41.2833, 'lng': -72.9083},
    {'id': '8467150', 'name': 'Bridgeport', 'lat': 41.1758, 'lng': -73.184},
    {'id': '8510560', 'name': 'Montauk', 'lat': 41.0483, 'lng': -71.9594},
    {'id': '8516945', 'name': 'Kings Point', 'lat': 40.8103, 'lng': -73.7649},
    {'id': '8517986', 'name': 'Verrazano-Narrows Air Gap', 'lat': 40.6062, 'lng': -74.0448},
    {'id': '8518750', 'name': 'The Battery', 'lat': 40.7006, 'lng': -74.0142},
    {'id': '8518962', 'name': 'Turkey Point Hudson River NERRS', 'lat': 42.0142, 'lng': -73.9392},
    {'id': '8519461', 'name': 'Bayonne Bridge Air Gap', 'lat': 40.642, 'lng': -74.1421},
    {'id': '8519483', 'name': 'Bergen Point West Reach', 'lat': 40.6391, 'lng': -74.1463},
    {'id': '8519532', 'name': 'Mariners Harbor', 'lat': 40.6383, 'lng': -74.16},
    {'id': '8530973', 'name': 'Robbins Reef', 'lat': 40.6584, 'lng': -74.0647},
    {'id': '8531680', 'name': 'Sandy Hook', 'lat': 40.4669, 'lng': -74.0094},
    {'id': '8534720', 'name': 'Atlantic City', 'lat': 39.3567, 'lng': -74.4181},
    {'id': '8536110', 'name': 'Cape May', 'lat': 38.9683, 'lng': -74.96},
    {'id': '8537121', 'name': 'Ship John Shoal', 'lat': 39.3054, 'lng': -75.3767},
    {'id': '8539094', 'name': 'Burlington, Delaware River', 'lat': 40.0817, 'lng': -74.8697},
    {'id': '8540433', 'name': 'Marcus Hook', 'lat': 39.8118, 'lng': -75.4095},
    {'id': '8545240', 'name': 'Philadelphia', 'lat': 39.9331, 'lng': -75.142},
    {'id': '8545556', 'name': 'Ben Franklin Bridge Air Gap', 'lat': 39.9528, 'lng': -75.1358},
    {'id': '8546252', 'name': 'Bridesburg', 'lat': 39.9797, 'lng': -75.0793},
    {'id': '8548989', 'name': 'Newbold', 'lat': 40.1373, 'lng': -74.7518},
    {'id': '8550959', 'name': 'Delaware Memorial Bridge Air Gap', 'lat': 39.6883, 'lng': -75.5183},
    {'id': '8551762', 'name': 'Delaware City', 'lat': 39.5822, 'lng': -75.589},
    {'id': '8551910', 'name': 'Reedy Point', 'lat': 39.5583, 'lng': -75.5719},
    {'id': '8551911', 'name': 'Reedy Point Air Gap', 'lat': 39.5583, 'lng': -75.5824},
    {'id': '8555889', 'name': 'Brandywine Shoal Light', 'lat': 38.987, 'lng': -75.113},
    {'id': '8557380', 'name': 'Lewes', 'lat': 38.7828, 'lng': -75.1193},
    {'id': '8570283', 'name': 'Ocean City Inlet', 'lat': 38.3283, 'lng': -75.0911},
    {'id': '8571421', 'name': 'Bishops Head', 'lat': 38.22, 'lng': -76.0383},
    {'id': '8571892', 'name': 'Cambridge', 'lat': 38.5725, 'lng': -76.0617},
    {'id': '8573364', 'name': 'Tolchester Beach', 'lat': 39.2134, 'lng': -76.2446},
    {'id': '8573927', 'name': 'Chesapeake City', 'lat': 39.5267, 'lng': -75.81},
    {'id': '8573928', 'name': 'Chesapeake City Air Gap', 'lat': 39.5292, 'lng': -75.8138},
    {'id': '8574680', 'name': 'Baltimore', 'lat': 39.27, 'lng': -76.5783},
    {'id': '8574728', 'name': 'Francis Scott Key Bridge', 'lat': 39.22, 'lng': -76.5283},
    {'id': '8574731', 'name': 'Hawkins Point Wind', 'lat': 39.2144, 'lng': -76.5317},
    {'id': '8575431', 'name': 'Bay Bridge (170ft East of Ctr) Air Gap', 'lat': 38.9931, 'lng': -76.3816},
    {'id': '8575432', 'name': 'Bay Bridge (Center Channel) Air Gap', 'lat': 38.9932, 'lng': -76.3822},
    {'id': '8575437', 'name': 'Chesapeake Bay Bridge Visibility', 'lat': 38.9948, 'lng': -76.3881},
    {'id': '8575512', 'name': 'Annapolis', 'lat': 38.9833, 'lng': -76.4816},
    {'id': '8577018', 'name': 'Cove Point LNG Pier', 'lat': 38.4044, 'lng': -76.3855},
    {'id': '8577330', 'name': 'Solomons Island', 'lat': 38.3167, 'lng': -76.4517},
    {'id': '8578240', 'name': 'Piney Point', 'lat': 38.1333, 'lng': -76.5333},
    {'id': '8594900', 'name': 'Washington', 'lat': 38.873, 'lng': -77.0217},
    {'id': '8631044', 'name': 'Wachapreague', 'lat': 37.6078, 'lng': -75.6858},
    {'id': '8632200', 'name': 'Kiptopeke', 'lat': 37.1653, 'lng': -75.9883},
    {'id': '8632837', 'name': 'Rappahannock Light', 'lat': 37.5383, 'lng': -76.015},
    {'id': '8635027', 'name': 'Dahlgren', 'lat': 38.3198, 'lng': -77.0366},
    {'id': '8635750', 'name': 'Lewisetta', 'lat': 37.9964, 'lng': -76.4656},
    {'id': '8636580', 'name': 'Windmill Point', 'lat': 37.6155, 'lng': -76.2898},
    {'id': '8637689', 'name': 'Yorktown USCG Training Center', 'lat': 37.2265, 'lng': -76.4788},
    {'id': '8638511', 'name': 'Dominion Terminal Associates', 'lat': 36.9623, 'lng': -76.4242},
    {'id': '8638595', 'name': 'South Craney Island', 'lat': 36.9, 'lng': -76.3386},
    {'id': '8638610', 'name': 'Sewells Point', 'lat': 36.9428, 'lng': -76.3286},
    {'id': '8638614', 'name': 'Willoughby Degaussing Station', 'lat': 36.9817, 'lng': -76.3217},
    {'id': '8638901', 'name': 'CBBT, Chesapeake Channel', 'lat': 37.0329, 'lng': -76.0833},
    {'id': '8638999', 'name': 'Cape Henry', 'lat': 36.93, 'lng': -76.0067},
    {'id': '8639348', 'name': 'Money Point', 'lat': 36.7782, 'lng': -76.3019},
    {'id': '8651370', 'name': 'Duck', 'lat': 36.1833, 'lng': -75.7467},
    {'id': '8652587', 'name': 'Oregon Inlet Marina', 'lat': 35.7957, 'lng': -75.5482},
    {'id': '8654467', 'name': 'USCG Station Hatteras', 'lat': 35.2086, 'lng': -75.7042},
    {'id': '8656483', 'name': 'Beaufort, Duke Marine Lab', 'lat': 34.7175, 'lng': -76.6711},
    {'id': '8658120', 'name': 'Wilmington', 'lat': 34.2275, 'lng': -77.9536},
    {'id': '8658163', 'name': 'Wrightsville Beach', 'lat': 34.2133, 'lng': -77.7867},
    {'id': '8661070', 'name': 'Springmaid Pier', 'lat': 33.655, 'lng': -78.9183},
    {'id': '8664753', 'name': 'Don Holt Bridge Air Gap', 'lat': 32.8912, 'lng': -79.9644},
    {'id': '8665353', 'name': 'Ravenel Bridge Air Gap', 'lat': 32.8031, 'lng': -79.9139},
    {'id': '8665530', 'name': 'Charleston', 'lat': 32.775, 'lng': -79.9239},
    {'id': '8670674', 'name': 'Talmadge Memorial Bridge Air Gap', 'lat': 32.0883, 'lng': -81.099},
    {'id': '8670870', 'name': 'Fort Pulaski', 'lat': 32.0347, 'lng': -80.903},
    {'id': '8679598', 'name': 'Kings Bay MSF Pier', 'lat': 30.7781, 'lng': -81.4914},
    {'id': '8720030', 'name': 'Fernandina Beach', 'lat': 30.6714, 'lng': -81.4658},
    {'id': '8720215', 'name': 'Navy Fuel Depot', 'lat': 30.4, 'lng': -81.6267},
    {'id': '8720218', 'name': 'Mayport (Bar Pilots Dock)', 'lat': 30.3982, 'lng': -81.4279},
    {'id': '8720219', 'name': 'Dames Point', 'lat': 30.3872, 'lng': -81.5592},
    {'id': '8720226', 'name': 'Southbank Riverwalk, St Johns River', 'lat': 30.3205, 'lng': -81.6591},
    {'id': '8720228', 'name': 'Little Jetties Visibility', 'lat': 30.3794, 'lng': -81.4461},
    {'id': '8720233', 'name': 'Blount Island Command', 'lat': 30.3925, 'lng': -81.5225},
    {'id': '8720245', 'name': 'Jacksonville University', 'lat': 30.3541, 'lng': -81.6118},
    {'id': '8720357', 'name': 'I-295 Buckman Bridge', 'lat': 30.1924, 'lng': -81.69},
    {'id': '8720376', 'name': 'Dames Point Bridge Air Gap', 'lat': 30.3845, 'lng': -81.5571},
    {'id': '8721604', 'name': 'Trident Pier, Port Canaveral', 'lat': 28.4158, 'lng': -80.5931},
    {'id': '8722670', 'name': 'Lake Worth Pier, Atlantic Ocean', 'lat': 26.6128, 'lng': -80.0342},
    {'id': '8722956', 'name': 'South Port Everglades', 'lat': 26.0817, 'lng': -80.1167},
    {'id': '8723214', 'name': 'Virginia Key', 'lat': 25.7317, 'lng': -80.1617},
    {'id': '8723970', 'name': 'Vaca Key, Florida Bay', 'lat': 24.711, 'lng': -81.1065},
    {'id': '8724580', 'name': 'Key West', 'lat': 24.5508, 'lng': -81.8083},
    {'id': '8725114', 'name': 'Naples Bay, North', 'lat': 26.1367, 'lng': -81.7883},
    {'id': '8725520', 'name': 'Fort Myers', 'lat': 26.648, 'lng': -81.871},
    {'id': '8726371', 'name': 'Sunshine Skyway Bridge Air Gap', 'lat': 27.6206, 'lng': -82.6558},
    {'id': '8726384', 'name': 'Port Manatee', 'lat': 27.6387, 'lng': -82.5621},
    {'id': '8726412', 'name': 'Middle Tampa Bay', 'lat': 27.6617, 'lng': -82.5994},
    {'id': '8726520', 'name': 'St. Petersburg', 'lat': 27.7606, 'lng': -82.6269},
    {'id': '8726524', 'name': 'Gadsden Cut, Tampa Bay', 'lat': 27.7735, 'lng': -82.5169},
    {'id': '8726607', 'name': 'Old Port Tampa', 'lat': 27.8578, 'lng': -82.5528},
    {'id': '8726671', 'name': 'Sparkman Channel Entrance', 'lat': 27.9206, 'lng': -82.4453},
    {'id': '8726674', 'name': 'East Bay', 'lat': 27.9231, 'lng': -82.4214},
    {'id': '8726679', 'name': 'East Bay Causeway', 'lat': 27.929, 'lng': -82.4257},
    {'id': '8726694', 'name': 'TPA Cruise Terminal 2', 'lat': 27.943, 'lng': -82.4459},
    {'id': '8726724', 'name': 'Clearwater Beach', 'lat': 27.9783, 'lng': -82.8317},
    {'id': '8727520', 'name': 'Cedar Key', 'lat': 29.135, 'lng': -83.0317},
    {'id': '8728690', 'name': 'Apalachicola', 'lat': 29.7244, 'lng': -84.9806},
    {'id': '8729108', 'name': 'Panama City', 'lat': 30.1497, 'lng': -85.6644},
    {'id': '8729210', 'name': 'Panama City Beach', 'lat': 30.2138, 'lng': -85.8786},
    {'id': '8729840', 'name': 'Pensacola', 'lat': 30.4044, 'lng': -87.2112},
    {'id': '8734383', 'name': 'Fort Morgan', 'lat': 30.2344, 'lng': -87.9936},
    {'id': '8734536', 'name': 'E Range Front Light Visibility', 'lat': 30.44, 'lng': -88.0096},
    {'id': '8735180', 'name': 'Dauphin Island', 'lat': 30.2503, 'lng': -88.075},
    {'id': '8735391', 'name': 'Dog River Bridge', 'lat': 30.5653, 'lng': -88.0881},
    {'id': '8735523', 'name': 'East Fowl River Bridge', 'lat': 30.4437, 'lng': -88.1139},
    {'id': '8736163', 'name': 'Middle Bay Port Visibility, Mobile Bay', 'lat': 30.5272, 'lng': -88.0861},
    {'id': '8736897', 'name': 'Coast Guard Sector Mobile', 'lat': 30.6495, 'lng': -88.0581},
    {'id': '8737005', 'name': 'Pinto Island Visibility', 'lat': 30.6712, 'lng': -88.031},
    {'id': '8737048', 'name': 'Mobile State Docks', 'lat': 30.7046, 'lng': -88.0396},
    {'id': '8737138', 'name': 'Chickasaw Creek', 'lat': 30.7819, 'lng': -88.0736},
    {'id': '8738043', 'name': 'West Fowl River Bridge', 'lat': 30.3766, 'lng': -88.1586},
    {'id': '8739803', 'name': 'Bayou La Batre Bridge', 'lat': 30.4062, 'lng': -88.2478},
    {'id': '8741003', 'name': 'Petit Bois Island, Port of Pascagoula', 'lat': 30.2133, 'lng': -88.5},
    {'id': '8741533', 'name': 'Pascagoula NOAA Lab', 'lat': 30.3678, 'lng': -88.5631},
    {'id': '8747437', 'name': 'Bay Waveland Yacht Club', 'lat': 30.3263, 'lng': -89.3258},
    {'id': '8760721', 'name': 'Pilottown', 'lat': 29.1793, 'lng': -89.2588},
    {'id': '8760922', 'name': 'Pilots Station East, S.W. Pass', 'lat': 28.9322, 'lng': -89.4075},
    {'id': '8761305', 'name': 'Shell Beach', 'lat': 29.8683, 'lng': -89.673},
    {'id': '8761724', 'name': 'Grand Isle', 'lat': 29.2633, 'lng': -89.9567},
    {'id': '8761847', 'name': 'Crescent City Air Gap', 'lat': 29.9383, 'lng': -90.0572},
    {'id': '8761927', 'name': 'New Canal Station', 'lat': 30.0272, 'lng': -90.1133},
    {'id': '8761955', 'name': 'Carrollton', 'lat': 29.9329, 'lng': -90.1355},
    {'id': '8762002', 'name': 'Huey Long Bridge Air Gap', 'lat': 29.9431, 'lng': -90.1681},
    {'id': '8762075', 'name': 'Port Fourchon, Belle Pass', 'lat': 29.1142, 'lng': -90.1992},
    {'id': '8762482', 'name': 'West Bank 1, Bayou Gauche', 'lat': 29.7886, 'lng': -90.4203},
    {'id': '8764044', 'name': 'Berwick, Atchafalaya River', 'lat': 29.6675, 'lng': -91.2376},
    {'id': '8764227', 'name': 'LAWMA, Amerada Pass', 'lat': 29.4496, 'lng': -91.3381},
    {'id': '8764314', 'name': 'Eugene Island, North of, Atchafalaya Bay', 'lat': 29.3675, 'lng': -91.3839},
    {'id': '8766072', 'name': 'Freshwater Canal Locks', 'lat': 29.5517, 'lng': -92.3053},
    {'id': '8767816', 'name': 'Lake Charles', 'lat': 30.2236, 'lng': -93.2217},
    {'id': '8767931', 'name': 'Lake Charles I-210 Bridge Air Gap', 'lat': 30.2017, 'lng': -93.2806},
    {'id': '8767961', 'name': 'Bulk Terminal', 'lat': 30.1903, 'lng': -93.3007},
    {'id': '8768094', 'name': 'Calcasieu Pass', 'lat': 29.7682, 'lng': -93.3429},
    {'id': '8770475', 'name': 'Port Arthur', 'lat': 29.8667, 'lng': -93.93},
    {'id': '8770520', 'name': 'Rainbow Bridge', 'lat': 29.9812, 'lng': -93.8847},
    {'id': '8770613', 'name': 'Morgans Point, Barbours Cut', 'lat': 29.6817, 'lng': -94.985},
    {'id': '8770777', 'name': 'Manchester', 'lat': 29.7263, 'lng': -95.2658},
    {'id': '8770808', 'name': 'High Island', 'lat': 29.5947, 'lng': -94.3903},
    {'id': '8770822', 'name': 'Texas Point, Sabine Pass', 'lat': 29.6893, 'lng': -93.8418},
    {'id': '8770971', 'name': 'Rollover Pass', 'lat': 29.515, 'lng': -94.5133},
    {'id': '8771013', 'name': 'Eagle Point, Galveston Bay', 'lat': 29.4813, 'lng': -94.9173},
    {'id': '8771341', 'name': 'Galveston Bay Entrance, North Jetty', 'lat': 29.3575, 'lng': -94.7247},
    {'id': '8771367', 'name': 'Sabine Offshore Light', 'lat': 29.469, 'lng': -93.72},
    {'id': '8771450', 'name': 'Galveston Pier 21', 'lat': 29.31, 'lng': -94.7933},
    {'id': '8771486', 'name': 'Galveston Railroad Bridge', 'lat': 29.3026, 'lng': -94.8971},
    {'id': '8771972', 'name': 'San Luis Pass', 'lat': 29.0806, 'lng': -95.1308},
    {'id': '8772471', 'name': 'Freeport Harbor', 'lat': 28.9357, 'lng': -95.2942},
    {'id': '8772985', 'name': 'Sargent', 'lat': 28.7714, 'lng': -95.6175},
    {'id': '8773037', 'name': 'Seadrift', 'lat': 28.4069, 'lng': -96.7124},
    {'id': '8773146', 'name': 'Matagorda City', 'lat': 28.71, 'lng': -95.914},
    {'id': '8773259', 'name': 'Port Lavaca', 'lat': 28.6406, 'lng': -96.6098},
    {'id': '8773701', 'name': "Port O'Connor", 'lat': 28.4517, 'lng': -96.3883},
    {'id': '8773767', 'name': 'Matagorda Bay Entrance Channel', 'lat': 28.4269, 'lng': -96.3301},
    {'id': '8774230', 'name': 'Aransas Wildlife Refuge', 'lat': 28.2283, 'lng': -96.795},
    {'id': '8774770', 'name': 'Rockport', 'lat': 28.0217, 'lng': -97.0467},
    {'id': '8775132', 'name': 'La Quinta Channel North', 'lat': 27.8792, 'lng': -97.2861},
    {'id': '8775222', 'name': 'Viola Turning Basin', 'lat': 27.8461, 'lng': -97.5207},
    {'id': '8775223', 'name': 'Harbor Island Visibility', 'lat': 27.844, 'lng': -97.0696},
    {'id': '8775236', 'name': 'UTMSI Visibility', 'lat': 27.8383, 'lng': -97.0522},
    {'id': '8775237', 'name': 'Port Aransas', 'lat': 27.8398, 'lng': -97.0728},
    {'id': '8775241', 'name': 'Aransas, Aransas Pass', 'lat': 27.8366, 'lng': -97.0391},
    {'id': '8775244', 'name': 'Nueces Bay', 'lat': 27.8328, 'lng': -97.4859},
    {'id': '8775283', 'name': 'Enbridge, Ingleside', 'lat': 27.8186, 'lng': -97.2089},
    {'id': '8775285', 'name': 'Tule Lake Visibility', 'lat': 27.8194, 'lng': -97.4537},
    {'id': '8775296', 'name': 'USS Lexington, Corpus Christi Bay', 'lat': 27.8117, 'lng': -97.39},
    {'id': '8775302', 'name': 'Texas State Aquarium Visibility', 'lat': 27.8125, 'lng': -97.3886},
    {'id': '8775792', 'name': 'Packery Channel', 'lat': 27.6333, 'lng': -97.2367},
    {'id': '8776139', 'name': 'S. Bird Island', 'lat': 27.4844, 'lng': -97.3181},
    {'id': '8776604', 'name': 'Baffin Bay', 'lat': 27.297, 'lng': -97.4052},
    {'id': '8777812', 'name': 'Rincon Del San Jose', 'lat': 26.8012, 'lng': -97.4706},
    {'id': '8778490', 'name': 'Port Mansfield', 'lat': 26.5576, 'lng': -97.4257},
    {'id': '8779280', 'name': 'Realitos Peninsula', 'lat': 26.2625, 'lng': -97.2853},
    {'id': '8779748', 'name': 'South Padre Island CG Station', 'lat': 26.0725, 'lng': -97.1669},
    {'id': '8779749', 'name': 'SPI Brazos Santiago', 'lat': 26.0675, 'lng': -97.1547},
    {'id': '8779770', 'name': 'Port Isabel', 'lat': 26.0612, 'lng': -97.2155},
    {'id': '9014070', 'name': 'Algonac', 'lat': 42.6211, 'lng': -82.5267},
    {'id': '9014080', 'name': 'St. Clair State Police', 'lat': 42.8122, 'lng': -82.4856},
    {'id': '9014087', 'name': 'Dry Dock', 'lat': 42.9453, 'lng': -82.4433},
    {'id': '9014090', 'name': 'Mouth of the Black River', 'lat': 42.9747, 'lng': -82.4189},
    {'id': '9014098', 'name': 'Fort Gratiot', 'lat': 43.0069, 'lng': -82.4225},
    {'id': '9034052', 'name': 'St Clair Shores', 'lat': 42.4732, 'lng': -82.8792},
    {'id': '9044020', 'name': 'Gibraltar', 'lat': 42.0909, 'lng': -83.186},
    {'id': '9044030', 'name': 'Wyandotte', 'lat': 42.2023, 'lng': -83.1475},
    {'id': '9044036', 'name': 'Fort Wayne', 'lat': 42.2989, 'lng': -83.0926},
    {'id': '9044049', 'name': 'Windmill Point', 'lat': 42.3578, 'lng': -82.9299},
    {'id': '9052000', 'name': 'Cape Vincent', 'lat': 44.1303, 'lng': -76.3322},
    {'id': '9052030', 'name': 'Oswego', 'lat': 43.4642, 'lng': -76.5118},
    {'id': '9052058', 'name': 'Rochester', 'lat': 43.269, 'lng': -77.6257},
    {'id': '9052076', 'name': 'Olcott', 'lat': 43.3384, 'lng': -78.7273},
    {'id': '9063007', 'name': 'Ashland Ave', 'lat': 43.1, 'lng': -79.0599},
    {'id': '9063009', 'name': 'American Falls', 'lat': 43.0811, 'lng': -79.0614},
    {'id': '9063012', 'name': 'Niagara Intake', 'lat': 43.0769, 'lng': -79.014},
    {'id': '9063020', 'name': 'Buffalo', 'lat': 42.8774, 'lng': -78.8905},
    {'id': '9063028', 'name': 'Sturgeon Point', 'lat': 42.6913, 'lng': -79.0473},
    {'id': '9063038', 'name': 'Erie, Lake Erie', 'lat': 42.1539, 'lng': -80.0758},
    {'id': '9063053', 'name': 'Fairport', 'lat': 41.7597, 'lng': -81.2811},
    {'id': '9063063', 'name': 'Cleveland', 'lat': 41.5409, 'lng': -81.6355},
    {'id': '9063079', 'name': 'Marblehead', 'lat': 41.5436, 'lng': -82.7314},
    {'id': '9063085', 'name': 'Toledo', 'lat': 41.6936, 'lng': -83.4723},
    {'id': '9063090', 'name': 'Fermi Power Plant', 'lat': 41.96, 'lng': -83.257},
    {'id': '9075002', 'name': 'Lakeport', 'lat': 43.1404, 'lng': -82.4939},
    {'id': '9075014', 'name': 'Harbor Beach', 'lat': 43.8462, 'lng': -82.6431},
    {'id': '9075035', 'name': 'Essexville', 'lat': 43.641, 'lng': -83.8464},
    {'id': '9075065', 'name': 'Alpena', 'lat': 45.063, 'lng': -83.4286},
    {'id': '9075080', 'name': 'Mackinaw City', 'lat': 45.7772, 'lng': -84.7211},
    {'id': '9075099', 'name': 'De Tour Village', 'lat': 45.9925, 'lng': -83.8982},
    {'id': '9076024', 'name': 'Rock Cut', 'lat': 46.2643, 'lng': -84.1912},
    {'id': '9076027', 'name': 'West Neebish Island', 'lat': 46.2847, 'lng': -84.2098},
    {'id': '9076033', 'name': 'Little Rapids', 'lat': 46.4858, 'lng': -84.3017},
    {'id': '9076060', 'name': 'U.S. Slip', 'lat': 46.5008, 'lng': -84.3404},
    {'id': '9076070', 'name': 'S.W. Pier, St. Marys River', 'lat': 46.5014, 'lng': -84.3725},
    {'id': '9087023', 'name': 'Ludington', 'lat': 43.9474, 'lng': -86.4415},
    {'id': '9087031', 'name': 'Holland', 'lat': 42.7733, 'lng': -86.2128},
    {'id': '9087044', 'name': 'Calumet Harbor', 'lat': 41.7299, 'lng': -87.5384},
    {'id': '9087057', 'name': 'Milwaukee', 'lat': 43.002, 'lng': -87.8876},
    {'id': '9087068', 'name': 'Kewaunee, Lake Michigan', 'lat': 44.4639, 'lng': -87.5111},
    {'id': '9087069', 'name': 'Kewaunee MET', 'lat': 44.465, 'lng': -87.4958},
    {'id': '9087072', 'name': 'Sturgeon Bay Canal', 'lat': 44.7947, 'lng': -87.3139},
    {'id': '9087077', 'name': 'Green Bay East', 'lat': 44.539, 'lng': -88.0011},
    {'id': '9087088', 'name': 'Menominee', 'lat': 45.0959, 'lng': -87.5899},
    {'id': '9087096', 'name': 'Port Inland', 'lat': 45.9699, 'lng': -85.8715},
    {'id': '9099004', 'name': 'Point Iroquois', 'lat': 46.4844, 'lng': -84.6308},
    {'id': '9099018', 'name': 'Marquette C.G.', 'lat': 46.5456, 'lng': -87.3786},
    {'id': '9099044', 'name': 'Ontonagon', 'lat': 46.8744, 'lng': -89.3242},
    {'id': '9099064', 'name': 'Duluth', 'lat': 46.7758, 'lng': -92.092},
    {'id': '9099090', 'name': 'Grand Marais, Lake Superior', 'lat': 47.7486, 'lng': -90.3413},
    {'id': '9410170', 'name': 'San Diego', 'lat': 32.7156, 'lng': -117.1767},
    {'id': '9410230', 'name': 'La Jolla', 'lat': 32.8669, 'lng': -117.2571},
    {'id': '9410647', 'name': 'Angels Gate', 'lat': 33.7158, 'lng': -118.2461},
    {'id': '9410660', 'name': 'Los Angeles', 'lat': 33.72, 'lng': -118.2719},
    {'id': '9410665', 'name': 'Long Beach Pier J', 'lat': 33.733, 'lng': -118.1857},
    {'id': '9410666', 'name': 'Los Angeles Pier 400', 'lat': 33.7352, 'lng': -118.2413},
    {'id': '9410670', 'name': 'Long Beach Pier F', 'lat': 33.7463, 'lng': -118.2156},
    {'id': '9410676', 'name': 'Vincent Thomas Bridge Air Gap', 'lat': 33.7494, 'lng': -118.2714},
    {'id': '9410689', 'name': 'Long Beach Intl. Gateway Bridge Air Gap', 'lat': 33.7645, 'lng': -118.221},
    {'id': '9410690', 'name': 'Los Angeles Berth 161', 'lat': 33.7636, 'lng': -118.2654},
    {'id': '9410691', 'name': 'Los Angeles Badger Avenue Bridge', 'lat': 33.7663, 'lng': -118.2401},
    {'id': '9410692', 'name': 'Long Beach Pier S', 'lat': 33.7683, 'lng': -118.2257},
    {'id': '9410840', 'name': 'Santa Monica', 'lat': 34.0083, 'lng': -118.5},
    {'id': '9411340', 'name': 'Santa Barbara', 'lat': 34.4046, 'lng': -119.6925},
    {'id': '9412110', 'name': 'Port San Luis', 'lat': 35.1689, 'lng': -120.7542},
    {'id': '9413450', 'name': 'Monterey', 'lat': 36.6089, 'lng': -121.8914},
    {'id': '9414290', 'name': 'San Francisco', 'lat': 37.8063, 'lng': -122.4659},
    {'id': '9414296', 'name': 'Pier 17 Visibility, San Francisco Bay', 'lat': 37.803, 'lng': -122.3971},
    {'id': '9414304', 'name': 'San Francisco-Oakland Bay Bridge Air Gap', 'lat': 37.8044, 'lng': -122.3728},
    {'id': '9414311', 'name': 'San Francisco Pier 1', 'lat': 37.798, 'lng': -122.393},
    {'id': '9414523', 'name': 'Redwood City', 'lat': 37.5068, 'lng': -122.2119},
    {'id': '9414750', 'name': 'Alameda', 'lat': 37.772, 'lng': -122.3003},
    {'id': '9414763', 'name': 'Oakland Berth 67', 'lat': 37.795, 'lng': -122.283},
    {'id': '9414769', 'name': 'Oakland Middle Harbor', 'lat': 37.8006, 'lng': -122.3297},
    {'id': '9414776', 'name': 'Oakland Berth 34', 'lat': 37.8106, 'lng': -122.3331},
    {'id': '9414797', 'name': 'Oakland Berth 38 Visibility', 'lat': 37.804, 'lng': -122.3417},
    {'id': '9414847', 'name': 'Point Potrero Richmond', 'lat': 37.9058, 'lng': -122.365},
    {'id': '9414863', 'name': 'Richmond', 'lat': 37.9283, 'lng': -122.4},
    {'id': '9415020', 'name': 'Point Reyes', 'lat': 37.9942, 'lng': -122.9736},
    {'id': '9415102', 'name': 'Martinez-Amorco Pier', 'lat': 38.0346, 'lng': -122.1252},
    {'id': '9415115', 'name': 'Pittsburg, Suisun Bay', 'lat': 38.0416, 'lng': -121.887},
    {'id': '9415118', 'name': 'Union Pacific Rail Road Bridge', 'lat': 38.0383, 'lng': -122.1205},
    {'id': '9415141', 'name': 'Davis Point', 'lat': 38.0567, 'lng': -122.2596},
    {'id': '9415144', 'name': 'Port Chicago', 'lat': 38.056, 'lng': -122.0395},
    {'id': '9416841', 'name': 'Arena Cove', 'lat': 38.9146, 'lng': -123.7111},
    {'id': '9418767', 'name': 'North Spit', 'lat': 40.7669, 'lng': -124.2173},
    {'id': '9418768', 'name': 'North Jetty Landing, Humboldt Bay', 'lat': 40.7689, 'lng': -124.239},
    {'id': '9419750', 'name': 'Crescent City', 'lat': 41.7456, 'lng': -124.1844},
    {'id': '9431647', 'name': 'Port Orford', 'lat': 42.739, 'lng': -124.4983},
    {'id': '9432780', 'name': 'Charleston', 'lat': 43.345, 'lng': -124.322},
    {'id': '9435380', 'name': 'South Beach', 'lat': 44.6254, 'lng': -124.0449},
    {'id': '9437540', 'name': 'Garibaldi', 'lat': 45.5545, 'lng': -123.9189},
    {'id': '9439040', 'name': 'Astoria', 'lat': 46.2073, 'lng': -123.7683},
    {'id': '9439099', 'name': 'Wauna', 'lat': 46.16, 'lng': -123.405},
    {'id': '9439201', 'name': 'St Helens', 'lat': 45.865, 'lng': -122.797},
    {'id': '9440083', 'name': 'Vancouver', 'lat': 45.6312, 'lng': -122.6958},
    {'id': '9440357', 'name': 'TEMCO Kalama Terminal', 'lat': 45.9839, 'lng': -122.8344},
    {'id': '9440422', 'name': 'Longview', 'lat': 46.1061, 'lng': -122.9542},
    {'id': '9440569', 'name': 'Skamokawa', 'lat': 46.2703, 'lng': -123.4565},
    {'id': '9440581', 'name': 'Cape Disappointment', 'lat': 46.281, 'lng': -124.0463},
    {'id': '9440910', 'name': 'Toke Point', 'lat': 46.7075, 'lng': -123.9669},
    {'id': '9441102', 'name': 'Westport', 'lat': 46.9043, 'lng': -124.1051},
    {'id': '9442396', 'name': 'La Push, Quillayute River', 'lat': 47.9128, 'lng': -124.6357},
    {'id': '9443090', 'name': 'Neah Bay', 'lat': 48.3708, 'lng': -124.6017},
    {'id': '9444090', 'name': 'Port Angeles', 'lat': 48.125, 'lng': -123.44},
    {'id': '9444900', 'name': 'Port Townsend', 'lat': 48.1112, 'lng': -122.7597},
    {'id': '9445958', 'name': 'Bremerton', 'lat': 47.5617, 'lng': -122.623},
    {'id': '9446482', 'name': 'Tacoma MET', 'lat': 47.276, 'lng': -122.418},
    {'id': '9446484', 'name': 'Tacoma', 'lat': 47.27, 'lng': -122.413},
    {'id': '9447130', 'name': 'Seattle', 'lat': 47.6028, 'lng': -122.3394},
    {'id': '9449419', 'name': 'Cherry Point South Dock', 'lat': 48.86, 'lng': -122.755},
    {'id': '9449424', 'name': 'Cherry Point', 'lat': 48.8627, 'lng': -122.7586},
    {'id': '9449427', 'name': 'Cherry Point North Dock', 'lat': 48.8642, 'lng': -122.7642},
    {'id': '9449880', 'name': 'Friday Harbor', 'lat': 48.5453, 'lng': -123.0125},
    {'id': '9450460', 'name': 'Ketchikan', 'lat': 55.3319, 'lng': -131.6261},
    {'id': '9451054', 'name': 'Port Alexander', 'lat': 56.2466, 'lng': -134.6477},
    {'id': '9451600', 'name': 'Sitka', 'lat': 57.0513, 'lng': -135.3435},
    {'id': '9452210', 'name': 'Juneau', 'lat': 58.2988, 'lng': -134.4106},
    {'id': '9452400', 'name': 'Skagway, Taiya Inlet', 'lat': 59.4508, 'lng': -135.328},
    {'id': '9452634', 'name': 'Elfin Cove', 'lat': 58.1947, 'lng': -136.3469},
    {'id': '9453220', 'name': 'Yakutat, Yakutat Bay', 'lat': 59.5483, 'lng': -139.7331},
    {'id': '9454050', 'name': 'Cordova', 'lat': 60.5575, 'lng': -145.7554},
    {'id': '9454240', 'name': 'Valdez', 'lat': 61.125, 'lng': -146.362},
    {'id': '9455090', 'name': 'Seward', 'lat': 60.1193, 'lng': -149.4281},
    {'id': '9455500', 'name': 'Seldovia', 'lat': 59.4405, 'lng': -151.7199},
    {'id': '9455760', 'name': 'Nikiski', 'lat': 60.6833, 'lng': -151.3981},
    {'id': '9455920', 'name': 'Anchorage', 'lat': 61.2375, 'lng': -149.8904},
    {'id': '9457292', 'name': 'Kodiak Island', 'lat': 57.7317, 'lng': -152.5119},
    {'id': '9457804', 'name': 'Alitak', 'lat': 56.8974, 'lng': -154.248},
    {'id': '9459450', 'name': 'Sand Point', 'lat': 55.3317, 'lng': -160.5043},
    {'id': '9459881', 'name': 'King Cove', 'lat': 55.0599, 'lng': -162.3261},
    {'id': '9461380', 'name': 'Adak Island', 'lat': 51.8606, 'lng': -176.6376},
    {'id': '9461710', 'name': 'Atka', 'lat': 52.2319, 'lng': -174.1725},
    {'id': '9462450', 'name': 'Nikolski', 'lat': 52.9406, 'lng': -168.8713},
    {'id': '9462620', 'name': 'Unalaska', 'lat': 53.8792, 'lng': -166.5403},
    {'id': '9463502', 'name': 'Port Moller', 'lat': 55.9858, 'lng': -160.5736},
    {'id': '9464212', 'name': 'Village Cove, St Paul Island', 'lat': 57.1253, 'lng': -170.2853},
    {'id': '9468333', 'name': 'Unalakleet', 'lat': 63.8714, 'lng': -160.7843},
    {'id': '9468756', 'name': 'Nome, Norton Sound', 'lat': 64.4946, 'lng': -165.4396},
    {'id': '9491094', 'name': 'Red Dog Dock', 'lat': 67.5758, 'lng': -164.0644},
    {'id': '9497645', 'name': 'Prudhoe Bay', 'lat': 70.4114, 'lng': -148.5317},
    {'id': '9751364', 'name': 'Christiansted Harbor, St Croix', 'lat': 17.7477, 'lng': -64.6984},
    {'id': '9751381', 'name': 'Lameshur Bay, St John', 'lat': 18.3182, 'lng': -64.7242},
    {'id': '9751401', 'name': 'Limetree Bay', 'lat': 17.6947, 'lng': -64.7538},
    {'id': '9751639', 'name': 'Charlotte Amalie', 'lat': 18.3306, 'lng': -64.9258},
    {'id': '9752235', 'name': 'Culebra', 'lat': 18.3009, 'lng': -65.3025},
    {'id': '9752621', 'name': 'Isabel Segunda, Vieques Island', 'lat': 18.1525, 'lng': -65.4438},
    {'id': '9752695', 'name': 'Esperanza, Vieques Island', 'lat': 18.0939, 'lng': -65.4714},
    {'id': '9753216', 'name': 'Fajardo', 'lat': 18.3353, 'lng': -65.6311},
    {'id': '9754229', 'name': 'Yabucoa Harbor', 'lat': 18.0551, 'lng': -65.833},
    {'id': '9755371', 'name': 'San Juan, La Puntilla, San Juan Bay', 'lat': 18.4589, 'lng': -66.1164},
    {'id': '9755968', 'name': 'Salinas, Bahia de Jobos', 'lat': 17.9491, 'lng': -66.2259},
    {'id': '9757811', 'name': 'Arecibo', 'lat': 18.4805, 'lng': -66.7024},
    {'id': '9758066', 'name': 'Guayanilla, Bahia de Guayanilla', 'lat': 18.0059, 'lng': -66.7666},
    {'id': '9759110', 'name': 'Magueyes Island', 'lat': 17.9701, 'lng': -67.0464},
    {'id': '9759394', 'name': 'Mayaguez', 'lat': 18.2188, 'lng': -67.1624},
    {'id': '9759413', 'name': 'Aguadilla, Crashboat Beach', 'lat': 18.4566, 'lng': -67.1646},
    {'id': '9759938', 'name': 'Mona Island', 'lat': 18.0893, 'lng': -67.9382}
]
