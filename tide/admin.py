# File: admin.py
# Author: Paul Martin Enano (enano1@bu.edu) November 11th, 2024
# Description: This file contains the code for the admin page.

from django.contrib import admin
from .models import *
# Register your models here.)

admin.site.register(Profile)
admin.site.register(Comment)
admin.site.register(Friend)
admin.site.register(StatusMessage)
admin.site.register(Image)
admin.site.register(SurfSession)
admin.site.register(SurfSpot)
