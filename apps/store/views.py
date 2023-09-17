from webbrowser import get
from django.shortcuts import render, redirect,get_object_or_404
from django.views import generic
from .models import *
from django.conf import settings
from django.db.models import Count
from django.db.models import Avg
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
from .forms import *
from datetime import datetime




def car_detail(request, slug, id):
    car = get_object_or_404(Car, slug=slug)  
    bids = car.bud_set.all()
    mapbox_access_token = settings.MAP_BOX_ACCESS_TOKEN 

    highest_bid = car.bud_set.all().order_by('bid_amount').last() 


    if request.method=='POST' and 'testdrive' in request.POST:
        name = request.POST.get('name', )
        email = request.POST.get('email', '')
        message = request.POST.get('message', '')
        date1_Y_m_d = request.POST.get('date1_Y_m_d', '')
        time1 = request.POST.get('time1', '')
        date2_Y_m_d = request.POST.get('date2_Y_m_d', '')
        time2 = request.POST.get('time2', '')

        testdrive = TestDrive.objects.create(
            car=car,
            name=name, 
            message=message, 
            email=email,
            date1_Y_m_d=date1_Y_m_d,
            time1=time1,
            date2_Y_m_d=date2_Y_m_d,
            time2=time2,
            )
        return redirect('/success/')

    if request.method=='POST' and 'make_bid' in request.POST:
        user = request.user
        bid_amount = request.POST.get('bid_amount', '')
        expiry_date = request.POST.get('expiry_date', '')

        car.bud_set.create(user=user, bid_amount=bid_amount, expiry_date=expiry_date)
        return redirect('/bid-sucessnkldsf2398ryoiqwepyr3829yr3982/')
    
    if request.method=='POST' and 'buy' in request.POST:
        user = request.user
        car = car
        car.sold = True
        car.save()

        buy = Buy.objects.create(user=user, car=car)
        return redirect('/min-bruker/mine-kjøp/')

    context = {
        'car': car,
        'bids': bids,
        'highest_bid': highest_bid,
        'mapbox_access_token': mapbox_access_token,
    }

    return render(request, 'core/product.html', context)

def bid_success(request):
    return render(request, 'core/bid-success.html')


def buy_car(request):
    cars = Car.objects.all()

    # Retrieve filtering options from query parameters
    price_order = request.GET.get('price_order')

    # Apply filters to the queryset
    if price_order == 'high_to_low':
        cars = cars.order_by('-price')
    elif price_order == 'low_to_high':
        cars = cars.order_by('price')

    if price_order == 'newest_to_oldest':
        cars = cars.order_by('-year')
    elif price_order == 'oldest_to_newest':
        cars = cars.order_by('year')

    if price_order == 'km_high_to_low':
        cars = cars.order_by('km')
    elif price_order == 'km_low_to_high':
        cars = cars.order_by('-km')

    context = {
        'cars': cars,
    }
    return render(request, 'core/buy.html', context)


@csrf_exempt
def home_page_search(request):
    query = request.GET.get('q','')
    if query:
        queryset = (
            Q(name__icontains=query) |
            Q(car_model__icontains=query) |
            Q(description__icontains=query) |
            Q(adress__icontains=query)
        )

        results = Car.objects.filter(queryset)
    else:
       results = []
    return render(request, 'core/search-results.html', {'results':results, 'query':query})

    #You can also set context = {'results':results, 'query':query} after 
    #the else: (same indentation as return statement), and 
    #use render(request, 'home.html', context) if you prefer. 
