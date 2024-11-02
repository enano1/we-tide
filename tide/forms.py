# forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Profile

class CreateProfileForm(forms.ModelForm):
    username = forms.CharField(label="Username", max_length=150, required=True)
    password = forms.CharField(label="Password", widget=forms.PasswordInput, required=True)
    password_confirmation = forms.CharField(label="Confirm Password", widget=forms.PasswordInput, required=True)
    
    fname = forms.CharField(label="First Name", max_length=100, required=True)
    lname = forms.CharField(label="Last Name", max_length=100, required=True)
    city = forms.CharField(label="City", max_length=100, required=True)
    email = forms.EmailField(label="Email", required=True)
    image = forms.ImageField(label="Profile Image", required=False)  # File upload for profile image

    class Meta:
        model = Profile
        fields = ['username', 'password', 'password_confirmation', 'fname', 'lname', 'city', 'email', 'image']
        
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        password_confirmation = cleaned_data.get("password_confirmation")
        
        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            self.add_error('username', "This username is already taken.")
        
        # Check if passwords match
        if password and password_confirmation and password != password_confirmation:
            self.add_error('password_confirmation', "Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        # Create the user
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        
        # Create the profile and associate it with the user
        profile = super().save(commit=False)
        profile.user = user
        if commit:
            profile.save()
        return profile
