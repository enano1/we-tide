from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from .models import Profile
from .forms import CreateProfileForm
from django.urls import reverse_lazy

# Display all profiles
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from .models import Profile

# View to show all profiles
# views.py
from django.shortcuts import redirect

class ShowAllProfilesView(ListView):
    model = Profile
    template_name = 'tide/show_all_profiles.html'
    context_object_name = 'profiles'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if the logged-in user has a profile (optional if you need it)
        if self.request.user.is_authenticated:
            context['has_profile'] = Profile.objects.filter(user=self.request.user).exists()
        return context
    
# View to show a single profile
class ShowProfilePageView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'tide/show_profile.html'  # Update to match your app name
    context_object_name = 'profile'
    login_url = '/login/'

# views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.shortcuts import redirect
from .models import Profile
from .forms import CreateProfileForm
from django.urls import reverse_lazy
from django.contrib.auth import login

# views.py
from django.urls import reverse
from django.views.generic.edit import CreateView
from .models import Profile
from .forms import CreateProfileForm

class CreateProfileView(CreateView):
    model = Profile
    form_class = CreateProfileForm
    template_name = 'tide/create_profile.html'

    def form_valid(self, form):
        # Save the form to create the user and profile
        self.object = form.save()
        
        # Redirect to the profile page of the created user
        return redirect('show_profile', pk=self.object.pk)  # Redirect to the specific profile's detail view
