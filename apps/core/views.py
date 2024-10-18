import warnings
import random
import requests


from urllib import *
from django.shortcuts import *

from django.shortcuts import *
from django.http import *
from django.core.mail import *
from django.contrib.auth import *
from django.template.loader import *
from textwrap import *
from django.views.decorators.csrf import *
from django.db.models import * 
from django.contrib.auth.decorators import *
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import *
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect
from .models import *
from datetime import datetime
from django.http import HttpResponseForbidden
from django.conf import settings
from datetime import date
from django.contrib.auth.models import User
from apps.store.models import *
from django.utils import translation


def home(request):
    # Get the language from the URL parameters first
    lang_code = request.LANGUAGE_CODE  # Get the active language code
    translation.activate(lang_code)  # Activate the language for the session
    return render(request, 'core/home.html', {'language': lang_code})

def set_language(request, language):
    # Set the language in a cookie
    response = redirect(request.META.get('HTTP_REFERER', 'home'))  # Redirect back to the previous page or home    
    response.set_cookie('language', language, max_age=365*24*60*60, path='/')  # Set the cookie for the entire site    
    translation.activate(language)  # Activate the language for the session
    return response


def contact(request):      
    return render(request, 'pages/contact/contact.html')  

def about(request):      
    return render(request, 'pages/about/about.html')  
