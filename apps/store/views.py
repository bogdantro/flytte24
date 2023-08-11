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
    product = get_object_or_404(Product, slug=slug)  
    mapbox_access_token = settings.MAP_BOX_ACCESS_TOKEN 

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    if request.method == 'POST':
        stars = request.POST.get('stars', )
        title = request.POST.get('title', '')
        content = request.POST.get('content', '')

        review = ProductReview.objects.create(product=product, stars=stars, title=title, content=content)

        return redirect('product_detail', slug=slug)

    context = {
        'product': product,
        'mapbox_access_token': mapbox_access_token,
        'num_visits': num_visits,
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
    return render(request, 'core/buy.html')