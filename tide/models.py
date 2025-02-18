# File: models.py
# Author: Paul Martin Enano (enano1@bu.edu) November 11th, 2024
# Description: This file contains the models for the We Tide application.

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
# forms.py


##############################################################################################
######################################## USER MODELS #########################################
##############################################################################################

class Profile(models.Model):
    """
    Model to encapsulate the idea of a Profile associated with a User.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Each user has one profile

    fname = models.CharField(max_length=100)  
    lname = models.CharField(max_length=100) 
    city = models.CharField(max_length=100)  
    email = models.EmailField()              
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)  
    bio = models.TextField(default="This is where you can add a bio or description about the user.", blank=True)


    def __str__(self):
        """
        Return a string representation of the Profile object.
        """
        return f"{self.fname} {self.lname}"

    def add_friend(self, other):
        """Add another profile as a friend if no duplicate relationship exists."""
        if self == other:
            return

        existing_friendship = Friend.objects.filter(
            models.Q(profile1=self, profile2=other) | models.Q(profile1=other, profile2=self)
        ).exists()

        if not existing_friendship:
            Friend.objects.create(profile1=self, profile2=other)

    def remove_friend(self, other):
        """Remove a friend relationship if it exists."""
        Friend.objects.filter(
            models.Q(profile1=self, profile2=other) | models.Q(profile1=other, profile2=self)
        ).delete()


    def get_friends(self):
        """Retrieve all friends of this profile."""
        friends = Friend.objects.filter(models.Q(profile1=self) | models.Q(profile2=self))
        return [f.profile2 if f.profile1 == self else f.profile1 for f in friends]

    def get_friend_suggestions(self):
        """Get friend suggestions for this profile."""
        friends = self.get_friends()
        all_profiles = Profile.objects.exclude(pk=self.pk)
        suggested_friends = all_profiles.exclude(pk__in=[friend.pk for friend in friends])
        return suggested_friends
    
    def get_news_feed(self):
        """Retrieve status messages for the current profile's friends and non-friends, excluding the current profile's own posts."""
        
        friends = self.get_friends()
        
        return StatusMessage.objects.filter(
            models.Q(profile__in=friends) | 
            models.Q(profile__in=Profile.objects.exclude(pk=self.pk))
        ).exclude(profile=self).order_by('-timestamp')


    def get_status_messages(self):
        return StatusMessage.objects.filter(profile=self).order_by('-timestamp')

    def get_surf_sessions(self):
        return SurfSession.objects.filter(profile=self).order_by('-date')
    
class Friend(models.Model):
    """Model to represent a friendship relationship between two profiles."""
    profile1 = models.ForeignKey(Profile, related_name="profile1_friends", on_delete=models.CASCADE)
    profile2 = models.ForeignKey(Profile, related_name="profile2_friends", on_delete=models.CASCADE)

    class Meta:
        unique_together = ('profile1', 'profile2')

##############################################################################################
######################################## SURF MODELS #########################################
##############################################################################################


class SurfSpot(models.Model):
    """Model representing a surf spot with associated user and location details."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surf_spots')
    station_id = models.CharField(max_length=10)
    nickname = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nickname or self.station_id}"
    
    class Meta:
        ordering = ['-created_at']
class SurfSession(models.Model):
    """Model to represent a surf session for a user."""
    
    surf_spot = models.ForeignKey(SurfSpot, on_delete=models.CASCADE, related_name='surf_sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surf_sessions')
    date = models.DateField()
    duration = models.DurationField()  
    wave_rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    notes = models.TextField(blank=True, max_length=100)

    def __str__(self):
        return f"Session at {self.surf_spot} on {self.date}, Rating: {self.wave_rating}"
    
    def get_absolute_url(self):
        return reverse('surf_sessions') 


##############################################################################################
#####################################$# SOCIAL MODELS ########################################
##############################################################################################

class StatusMessage(models.Model):
    """Model to store status messages, which are text updates from users."""
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='status_messages')
    surf_session = models.OneToOneField(SurfSession, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.timestamp} - {self.message[:20]}..."
        
    def get_images(self):
        '''Return all images associated with this StatusMessage.'''
        return self.images.all()  
    
    def get_absolute_url(self):
        return reverse('show_profile', kwargs={'pk': self.profile.pk})

    
class Image(models.Model):
    '''
    Encapsulate the idea of an image attached to a StatusMessage.
    '''
    image_file = models.ImageField(upload_to='images/') 
    status_message = models.ForeignKey('StatusMessage', on_delete=models.CASCADE, related_name='images')  
    def __str__(self):
        return f"Image {self.id} for StatusMessage {self.status_message.id}"
    
class Comment(models.Model): 
    '''
    A comment on a status message or post
    '''
    status_message = models.ForeignKey('StatusMessage', on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', null=True, blank=True)
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='comments')
    comment_text = models.TextField()

    def __str__(self):
        return f"Comment {self.id} on StatusMessage {self.status_message.id}"



    

