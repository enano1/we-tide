from django.db import models
from django.contrib.auth.models import User

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


class Friend(models.Model):
    """Model to represent a friendship relationship between two profiles."""
    profile1 = models.ForeignKey(Profile, related_name="profile1_friends", on_delete=models.CASCADE)
    profile2 = models.ForeignKey(Profile, related_name="profile2_friends", on_delete=models.CASCADE)

    class Meta:
        unique_together = ('profile1', 'profile2')