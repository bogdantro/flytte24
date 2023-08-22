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




def car_detail(request, slug):
    car = get_object_or_404(Car, slug=slug)  
    bids = car.bud_set.all()

    highest_bid = car.bud_set.all().order_by('bid_amount').last() 


    if request.method=='POST' and 'testdrive' in request.POST:
        name = request.POST.get('name', )
        email = request.POST.get('email', '')
        message = request.POST.get('message', '')
        date1 = request.POST.get('date1', '')
        fra_1 = request.POST.get('fra_1', '')
        til_1 = request.POST.get('til_1', '')
        date2 = request.POST.get('date2', '')
        fra_2 = request.POST.get('fra_2', '')
        til_2 = request.POST.get('til_2', '')

        testdrive = TestDrive.objects.create(
            name=name, 
            message=message, 
            email=email,
            date1=date1,
            fra_1=fra_1,
            til_1=til_1,
            date2=date2,
            fra_2=fra_2,
            til_2=til_2,
            )
        return redirect('/success/')

    if request.method=='POST' and 'make_bid' in request.POST:
        user = request.user
        bid_amount = request.POST.get('bid_amount', '')
        expiry_date = request.POST.get('expiry_date', '')

        car.bud_set.create(user=user, bid_amount=bid_amount, expiry_date=expiry_date)
        return redirect('/')

    context = {
        'car': car,
        'bids': bids,
        'highest_bid': highest_bid,
    }

    return render(request, 'core/product.html', context)

def buy_car(request):
    car = Car.objects.all() 

    context = {
        'car': car,
    }
    return render(request, 'core/buy.html', context)

