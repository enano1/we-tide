# File: admin.py
# Author: Paul Martin Enano (enano1@bu.edu) November 11th, 2024
# Description: App configuration for the Tide app.

from django.apps import AppConfig


class TideConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tide'
