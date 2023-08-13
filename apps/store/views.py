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


def product_detail(request, slug):
    car = get_object_or_404(Car, slug=slug)  

    context = {
        'car': car,
    }

    return render(request, 'core/product.html', context)

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)  
    product = Product.objects.filter(category=category)
    mapbox_access_token = settings.MAP_BOX_ACCESS_TOKEN 

    context = {
        'category': category,
        'product': product,
        'mapbox_access_token': mapbox_access_token,
    }

    return render(request, 'core/category.html', context)


def buy_car(request):
    car = Car.objects.all() 

    context = {
        'car': car,
    }
    return render(request, 'core/buy.html', context)