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
from django.shortcuts import render, redirect
from .forms import *
from .models import *
from datetime import datetime
from django.http import HttpResponseForbidden
from django.conf import settings
from datetime import date
from django.contrib.auth.models import User


def home(request):      
    mapbox_access_token = settings.MAP_BOX_ACCESS_TOKEN 

    locations = Location.objects.all()

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
    
    context = {
        'locations': locations,
        'mapbox_access_token': mapbox_access_token
    }
    return render(request, 'core/home.html', context)  


def sell(request):      
    return render(request, 'pages/book/sell.html')  



def book_time(request):
    
    if request.method == 'POST':
        date = request.POST.get('date', )
        time = request.POST.get('time', '')
        location = request.POST.get('location', '')
        preference = request.POST.get('preference', '')
        user = request.POST.get('user', '')
        full_name = request.POST.get('full_name', '')
        email = request.POST.get('email', '')
        mobile_number = request.POST.get('mobile_number', '')
        reg_number = request.POST.get('reg_number', '')
        km = request.POST.get('km', '')
        car_name_model = request.POST.get('car_name_model', '')
        sms_reminder = request.POST.get('sms_reminder', '')
        car_younger_than_10 = request.POST.get('car_younger_than_10', '')
        less_than_150000km = request.POST.get('less_than_150000km', '')
        vilkaar = request.POST.get('vilkaar', '')

        try:
            user_instance = User.objects.get(username=user)
        except User.DoesNotExist:
            return render(request, 'pages/book/error.html', {'message': 'User not found'})

        if Booking.objects.filter(date=date, time=time, is_booked=True).exists():
            return render(request, 'pages/book/error.html', {'message': 'This time slot is already booked!'})
        else:
            if sms_reminder == 'on':
                sms_reminder = True
            else:
                sms_reminder = False

            if car_younger_than_10 == 'on':
                car_younger_than_10 = True
            else:
                car_younger_than_10 = False

            if less_than_150000km == 'on':
                less_than_150000km = True
            else:

                less_than_150000km = False
            if vilkaar == 'on':
                vilkaar = True
            else:
                vilkaar = False
            booking = Booking.objects.create(user=user_instance, time=time, date=date, location=location, preference=preference, full_name=full_name, email=email, mobile_number=mobile_number, reg_number=reg_number, km=km, car_name_model=car_name_model, sms_reminder=sms_reminder, car_younger_than_10=car_younger_than_10, less_than_150000km=less_than_150000km, vilkaar=vilkaar)
            booking.is_booked = True
            booking.save()
        return render(request, 'pages/book/book-success.html', {'booking': booking})

    return render(request, 'pages/book/book.html')

def un_book(request):
    if request.method=='POST' and 'un_book' in request.POST:
        full_name = request.POST.get('full_name', )
        email = request.POST.get('email', '')
        message = request.POST.get('message', '')

        unbook = UnBook.objects.create(full_name=full_name, message=message, email=email)
        return redirect('success')
    return render(request, 'pages/book/un-book.html') 

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



def about(request):
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
    return render(request, 'pages/about/about.html')


def personerk(request):
    return render(request, 'pages/legal/personerk.html')

def salgvilkaar(request):
    return render(request, 'pages/legal/salgv.html')



def price(request):
    return render(request, 'pages/prices/price.html')