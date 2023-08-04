import warnings
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
from .forms import *
from django.utils import timezone
from datetime import timedelta
from .utils import *  # Import the function from utils.py
from django.shortcuts import render, redirect
from .forms import *
from .models import *
from datetime import datetime
from django.http import HttpResponseForbidden

def home(request):      
    if request.method=='POST' and 'verdivurdering' in request.POST:
        name = request.POST.get('name', )
        email = request.POST.get('email', '')
        telefon = request.POST.get('telefon', '')
        vilkaar = request.POST.get('vilkaar', '')
        reg_nr = request.POST.get('reg_nr', '')
        km = request.POST.get('km', '')
        if vilkaar == 'on':
            vilkaar = True
        else:
            vilkaar = False

        verdivurdering = Verdivurdering.objects.create(name=name, telefon=telefon, email=email, vilkaar=vilkaar, reg_nr=reg_nr, km=km)
        return redirect('success')
    return render(request, 'core/home.html')  


def sell(request):      
    return render(request, 'pages/book/sell.html')  

def book_time(request):

    return render(request, 'pages/book/book.html')

def success(request):
    return render(request, 'pages/contact/success.html')

def contact(request):
    if request.method=='POST' and 'contact' in request.POST:
        name = request.POST.get('name', )
        email = request.POST.get('email', '')
        message = request.POST.get('message', '')

        contact = Contact.objects.create(name=name, message=message, email=email)
        return redirect('success')
    return render(request, 'pages/contact/contact.html')  


def verdivurdering(request):
    if request.method=='POST' and 'verdivurdering' in request.POST:
        name = request.POST.get('name', )
        email = request.POST.get('email', '')
        telefon = request.POST.get('telefon', '')
        vilkaar = request.POST.get('vilkaar', '')
        reg_nr = request.POST.get('reg_nr', '')
        km = request.POST.get('km', '')
        if vilkaar == 'on':
            vilkaar = True
        else:
            vilkaar = False

        verdivurdering = Verdivurdering.objects.create(name=name, telefon=telefon, email=email, vilkaar=vilkaar, reg_nr=reg_nr, km=km)
        return redirect('success')
    return render(request, 'pages/contact/verdivurdering.html')  