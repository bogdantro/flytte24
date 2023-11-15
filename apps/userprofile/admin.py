from django.contrib import admin
from .models import Userprofile
from apps.core.models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class ProfileInline(admin.StackedInline):  # You can use admin.TabularInline for a more compact display
    model = Profile


class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]

admin.site.unregister(User)  # Unregister the default User admin
admin.site.register(User, CustomUserAdmin)  # Register the User admin with the inline

