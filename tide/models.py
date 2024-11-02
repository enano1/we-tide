from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    """
    Model to encapsulate the idea of a Profile associated with a User.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Each user has one profile

    fname = models.CharField(max_length=100)  # First name (required)
    lname = models.CharField(max_length=100)  # Last name (required)
    city = models.CharField(max_length=100)   # City (required)
    email = models.EmailField()               # Email (required)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)  # Profile image file (optional)

    def __str__(self):
        """
        Return a string representation of the Profile object.
        """
        return f"{self.fname} {self.lname}"
