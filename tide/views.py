from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from .models import Profile, StatusMessage, Image
from .forms import CreateProfileForm, UpdateProfileForm, CreateStatusMessageForm

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
