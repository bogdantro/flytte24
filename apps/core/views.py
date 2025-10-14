import warnings
import random
import requests
import json

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
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from apps.store.models import Bedrift_info
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

def home(request):

    return render(request, 'core/home.html')


from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Flytteforesporsel
from .forms import FlytteforesporselForm
from django.contrib.auth.decorators import login_required


def flytteforesporsel(request):
    return render(request, 'pages/about/flytteforesporsel.html')

from apps.store.models import Bedrift_info, JobDistribution

@csrf_exempt
@require_POST
def send_flytteforesporsel(request):

    data = json.loads(request.body.decode("utf-8"))

    # Opprett forespørsel
    inquiry = Flytteforesporsel.objects.create(
        move_type=data.get("move_type"),
        from_postcode=data.get("from_postcode"),
        from_city=data.get("from_city"),
        from_address=data.get("from_address"),
        to_postcode=data.get("to_postcode"),
        to_city=data.get("to_city"),
        to_address=data.get("to_address"),
        move_help=data.get("move_help"),
        from_property_type=data.get("from_property_type"),
        to_property_type=data.get("to_property_type"),
        from_rooms=data.get("from_rooms"),
        to_rooms=data.get("to_rooms"),
        additional_info=data.get("additional_info"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        phone=data.get("phone"),
        email=data.get("email"),
        consent=data.get("consent") == "true",
        created_at=timezone.now(),
    )

    # 🎯 Finn bedrifter som matcher både by OG flyttetype
    city = (data.get("from_city") or "").strip().lower()
    move_type = (data.get("move_type") or "").strip().lower()

    if city and move_type:
        all_businesses = Bedrift_info.objects.all()

        matching_businesses = []
        for b in all_businesses:
            # Sjekk by-match
            business_cities = [c.strip().lower() for c in (b.cities or "").split(",")]
            city_match = city in business_cities

            # Sjekk flyttetype-match
            business_move_types = [m.strip().lower() for m in (b.move_type or "").split(",")]
            move_match = move_type in business_move_types

            if city_match and move_match:
                matching_businesses.append(b)

        # Lagre distribusjon
        for business in matching_businesses:
            JobDistribution.objects.create(business=business, inquiry=inquiry)

    return JsonResponse({
        'success': True,
        'redirect_url': '/takk-for-din-foresporsel/'
    })

def for_business(request):      
    return render(request, 'pages/about/for-business.html') 



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def for_business_partner(request):
    if request.method == "POST":
        move_type = request.POST.getlist("moveType")
        cities = request.POST.getlist("city")

        data = Bedrift_info.objects.create(
            move_type=", ".join(move_type),
            cities=", ".join(cities),
            company_name=request.POST.get("companyName"),
            company_number=request.POST.get("companyNumber"),
            employees=request.POST.get("employees"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            website=request.POST.get("website"),
            address=request.POST.get("address"),
            postal_code=request.POST.get("postalCode"),
            city=request.POST.get("companyCity"),
            tiltaleform=request.POST.get("tiltaleform"),
            first_name=request.POST.get("firstName"),
            last_name=request.POST.get("lastName"),
        )

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "redirect_url": f"/reg/fullfor/lag-bruker/?email={data.email}"
            })


        # Normal form submit fallback
        return redirect(f"/reg/fullfor/lag-bruker/?email={data.email}")
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": False, "error": "Invalid request"})


    return render(request, "pages/about/for-business-partner.html")

def for_business(request):      
    return render(request, 'pages/about/for-business.html') 


def contact(request):      
    return render(request, 'pages/contact/contact.html')  

def about(request):      
    return render(request, 'pages/about/about.html')  
