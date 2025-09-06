# admin.py - Simple approach
from django.contrib import admin
from .models import Profile, Registration,Payment

# Register models with basic admin interface
models_to_register = [Profile, Registration,Payment]
admin.site.register(models_to_register)
