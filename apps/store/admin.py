from django.contrib import admin
from .models import *
from django import forms
from .widgets import WYMEditor
from .forms import *

# Register your models here.


class CarPostAdmin(admin.ModelAdmin):
    pass

admin.site.register(Car,CarPostAdmin)

    # list_display = ['name', 'business_name', 'slug', 'category', 'address', 'is_home_page',]
    # search_fields = ('name', 'business_name', 'slug', 'is_home_page', 'description')
    # list_filter = ('is_home_page',)
    # list_editable = ('is_home_page', 'business_name', 'slug', 'address', 'category',)
    # prepopulated_fields = {"slug": ("name","business_name",)}
