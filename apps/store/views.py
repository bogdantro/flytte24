import requests


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
from django.db.models import Q
from django.db.models import IntegerField
from django.db.models.functions import Replace, Cast




def update_bid_statuses(car):
    display_bids = car.bud_set.filter(Q(status='pending') | Q(status='accepted'))
    highest_bid = display_bids.order_by('-bid_amount').first()

    for bid in display_bids:
        if highest_bid is not None and bid.bid_amount < highest_bid.bid_amount:
            bid.status = 'declined'
            bid.save()



def car_bruksmerker(request, slug, id):
    car = get_object_or_404(Car, slug=slug, id=id)
    egenerkling_data = get_object_or_404(Egenerkeling, car=car)   

    context = {
        'car': car,
        'egenerkling_data': egenerkling_data,
    }
    return render(request, 'core/bruksmerker.html', context)


def car_detail(request, slug, id):
    car = get_object_or_404(Car, slug=slug, id=id)
    mapbox_access_token = settings.MAP_BOX_ACCESS_TOKEN
    num_active_images = car.num_active_images()

    if request.method == 'POST' and 'testdrive' in request.POST:
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        message = request.POST.get('message', '')
        phone_number = request.POST.get('phone_number', '')
        date1_Y_m_d = request.POST.get('date1_Y_m_d', '')
        time1 = request.POST.get('time1', '')
        date2_Y_m_d = request.POST.get('date2_Y_m_d', '')
        time2 = request.POST.get('time2', '')
        user_of_car = car.user
        user_data = {
            'id': user_of_car.id,
            'username': user_of_car.username,
            # Add more fields as needed
        }

        data = {
            'user': user_data,
            'car': car.to_dict(),
            'email': email,
            'message': message,
            'phone_number': phone_number,
            'date1_Y_m_d': date1_Y_m_d,
            'time1': time1,
            'date2_Y_m_d': date2_Y_m_d,
            'time2': time2,
        }   

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

        # Replace 'YOUR_ZAPIER_WEBHOOK_URL' with your actual Zapier webhook URL
        zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/13544280/3zxbt19/'

        # Make a POST request to Zapier webhook
        response = requests.post(zapier_webhook_url, json=data)

        return redirect('/success/')
    

    if request.method == 'POST' and 'make_bid' in request.POST:
        user = request.user
        user_of_car = car.user
        user_data = {
            'id': user_of_car.id,
            'username': user_of_car.username,
            # Add more fields as needed
        }

        bid_amount = int(request.POST.get('bid_amount', ''))
        expiry_date = request.POST.get('expiry_date', '')

        status = 'pending'

        data = {
            'user': user_data,
            'car': car.to_dict(),
            'bid_amount': bid_amount,
            'expiry_date': expiry_date,
        }   

        bid = car.bud_set.create(user=user, bid_amount=bid_amount, expiry_date=expiry_date, status=status)

        # Replace 'YOUR_ZAPIER_WEBHOOK_URL' with your actual Zapier webhook URL
        zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/13544280/3zxyd23/'

        # Make a POST request to Zapier webhook
        response = requests.post(zapier_webhook_url, json=data)


        update_bid_statuses(car)  # Update bid statuses after creating a new bid

        return redirect('/bid-sucessnkldsf2398ryoiqwepyr3829yr3982/')

    if request.method == 'POST' and 'buy' in request.POST:
        user = request.user
        user_of_car = car.user
        user_data = {
            'id': user_of_car.id,
            'username': user_of_car.username,
            # Add more fields as needed
        }
        car.sold = True
        car.save()

        buy = Buy.objects.create(user=user, car=car)

        data = {
            'carowner': user_data,
            'car': car.to_dict(),
        }   

        # Replace 'YOUR_ZAPIER_WEBHOOK_URL' with your actual Zapier webhook URL
        zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/13544280/3fjsana/'

        # Make a POST request to Zapier webhook
        response = requests.post(zapier_webhook_url, json=data)

        return redirect('/min-bruker/mine-kjøp/')

    update_bid_statuses(car)  # Update bid statuses before rendering the view

    display_bids = car.bud_set.filter(Q(status='pending') | Q(status='accepted'))
    highest_bid = display_bids.order_by('-bid_amount').first()

     # Calculate the status and days_until_expiry
    highest_bid_status = highest_bid.status if highest_bid else None
    days_until_expiry = highest_bid.days_until_expiry if highest_bid else None


    egenerkling_data = Egenerkeling.objects.filter(car=car)
 
    
    context = {
        'car': car,
        'bids': display_bids,
        'highest_bid': highest_bid,  # Pass the highest bid to the context
        'mapbox_access_token': mapbox_access_token,
        'highest_bid_status': highest_bid_status,
        'days_until_expiry': days_until_expiry,
        'egenerkling_data': egenerkling_data,
        'num_active_images': num_active_images,
    }
    return render(request, 'core/product.html', context)


def bid_success(request):
    return render(request, 'core/bid-success.html')


def buy_car(request):
    cars = Car.objects.filter(skjul_annonsen=False).order_by('-id')


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
        cars = cars.annotate(
            km_cleaned=Cast(
                Replace('km', Value(' '), Value(''), output_field=IntegerField()),
                output_field=IntegerField()
            )
        )
        cars = cars.order_by('-km_cleaned')
    elif price_order == 'km_low_to_high':
        cars = cars.annotate(
            km_cleaned=Cast(
                Replace('km', Value(' '), Value(''), output_field=IntegerField()),
                output_field=IntegerField()
            )
        )
        cars = cars.order_by('km_cleaned')



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
            Q(car_spesifikasjoner__icontains=query) |
            Q(car_brand__icontains=query) 
        )

        results = Car.objects.filter(queryset, skjul_annonsen=False)
    else:
       results = []
    return render(request, 'core/search-results.html', {'results':results, 'query':query})

    #You can also set context = {'results':results, 'query':query} after 
    #the else: (same indentation as return statement), and 
    #use render(request, 'home.html', context) if you prefer. 
