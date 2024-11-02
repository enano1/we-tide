from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, ListView, DetailView, CreateView
from .models import Profile
from .forms import CreateProfileForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from .models import Profile
from django.shortcuts import redirect

from tide import models

class ShowAllProfilesView(ListView):
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
        self.object = form.save()
        
        return redirect('show_profile', pk=self.object.pk) 

# views.py
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from .models import Profile
from .forms import UpdateProfileForm
from django.shortcuts import get_object_or_404

class UpdateProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = UpdateProfileForm
    template_name = 'tide/update_profile_form.html'

    def get_object(self, queryset=None):
        """Retrieve the profile object for the logged-in user based on the URL pk."""
        return get_object_or_404(Profile, pk=self.kwargs['pk'], user=self.request.user)

    def get_success_url(self):
        return reverse('show_profile', kwargs={'pk': self.object.pk})

from django.contrib import messages

class CreateFriendView(LoginRequiredMixin,View):
    def post(self, request, pk, other_pk):
        """Add a friend and redirect to profile page with a success message."""
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
