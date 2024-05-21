from django.contrib import admin
from .models import *
from django import forms
from .forms import *
from ckeditor.widgets import CKEditorWidget  # Import CKEditorWidget

# Register your models here.

admin.site.register(Membership)