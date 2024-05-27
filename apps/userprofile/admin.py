from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin



class ProfileInline(admin.StackedInline):  # You can use admin.TabularInline for a more compact display
    model = Profile


class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    list_filter = ['date_joined']  # Add the date_created field to filter users by creation date

admin.site.unregister(User)  # Unregister the default User admin
admin.site.register(User, CustomUserAdmin)  # Register the User admin with the inline
admin.site.register(Profile)  # Register the User admin with the inline
