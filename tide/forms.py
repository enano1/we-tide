# File: forms.py
# Author: Paul Martin Enano (enano1@bu.edu) November 11th, 2024
# Description: This module contains form definitions for creating and managing profiles, status messages, and other related entities.

from django import forms
from django.contrib.auth.models import User
from .models import Profile, StatusMessage, Image, SurfSession, Comment, SurfSpot

class CreateProfileForm(forms.ModelForm):
    """
    Form for creating a new profile. This form is used on the signup page.
    
    The form includes fields for the user's username, password, first name, last name, city, and bio.
    """
    username = forms.CharField(label="Username", max_length=150, required=True)
    password = forms.CharField(label="Password", widget=forms.PasswordInput, required=True)
    password_confirmation = forms.CharField(label="Confirm Password", widget=forms.PasswordInput, required=True)
    
    fname = forms.CharField(label="First Name", max_length=100, required=True)
    lname = forms.CharField(label="Last Name", max_length=100, required=True)
    city = forms.CharField(label="City", max_length=100, required=True)
    email = forms.EmailField(label="Email", required=True)
    image = forms.ImageField(label="Profile Image", required=False)  

    class Meta:
        model = Profile
        fields = ['username', 'password', 'password_confirmation', 'fname', 'lname', 'city', 'email', 'image']
        widgets = {
            'city': forms.TextInput(attrs={'placeholder': 'e.g., New York, NY, USA'}),
        }
        
    def clean(self):
        # Check if the username is already taken
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        password_confirmation = cleaned_data.get("password_confirmation")
        
        if User.objects.filter(username=username).exists():
            self.add_error('username', "This username is already taken.")
        
        if password and password_confirmation and password != password_confirmation:
            self.add_error('password_confirmation', "Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        # Create the user
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        
        profile = super().save(commit=False)
        profile.user = user
        if commit:
            profile.save()
        return profile
    
class UpdateProfileForm(forms.ModelForm):
    """
    Form for updating a user's profile information.

    This form allows users to update their city, email, profile image, and bio.
    It is associated with the Profile model.
    """
    class Meta:
        model = Profile
        fields = ['city', 'email', 'image', 'bio']

class CreateStatusMessageForm(forms.ModelForm):
    """
    Form for creating a new status message.

    This form allows users to create a new status message which can be
    associated with a surf session and have an image file. It is
    associated with the StatusMessage model.
    """
    surf_session = forms.ModelChoiceField(
        queryset=SurfSession.objects.all(),
        required=False,
        label="Related Surf Session"
    )
    image_file = forms.ImageField(required=False)

    class Meta:
        model = StatusMessage
        fields = ['message', 'surf_session', 'image_file']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['surf_session'].queryset = SurfSession.objects.filter(user=self.user)



class LocationForm(forms.Form):
    """
    Form for searching for tide data at a specific NOAA station.
    """
    station_id = forms.CharField(label="Station ID", max_length=10, required=True)

class SurfSessionForm(forms.ModelForm):
    """Form for creating or updating a surf session."""
    class Meta:
        model = SurfSession
        fields = ['surf_spot', 'date', 'duration', 'wave_rating', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'duration': forms.TextInput(attrs={'placeholder': 'e.g., 1:30:00 for 1 hour 30 minutes'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Additional notes... max of 100 characters'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)
        if user:
            self.fields['surf_spot'].queryset = SurfSpot.objects.filter(user=user)  

class CommentForm(forms.ModelForm):
    """Form for creating a new comment associated with a status message."""
    class Meta:
        model = Comment
        fields = ['comment_text']
        widgets = {
            'comment_text': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write a comment...'}),
        }