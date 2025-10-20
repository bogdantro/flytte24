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

import json, random
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from apps.core.models import Flytteforesporsel
from apps.store.models import Bedrift_info, JobDistribution



@csrf_exempt
@require_POST
def send_flytteforesporsel(request):
    """Create inquiry and distribute to matching businesses"""
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON."}, status=400)

    # 🗓 Parse date/time safely
    move_date_str = data.get("move_date")
    move_date = None
    if move_date_str:
        try:
            move_date = datetime.strptime(move_date_str, "%Y-%m-%d").date()
        except ValueError:
            move_date = None

    # 🧾 Create the inquiry
    inquiry = Flytteforesporsel.objects.create(
        move_type=data.get("move_type"),
        from_postcode=data.get("from_postcode"),
        from_city=data.get("from_city"),
        from_address=data.get("from_address"),
        from_property_type=data.get("from_property_type"),
        from_rooms=data.get("from_rooms"),
        from_kvm=data.get("from_kvm"),

        to_postcode=data.get("to_postcode"),
        to_city=data.get("to_city"),
        to_address=data.get("to_address"),
        to_property_type=data.get("to_property_type"),
        to_rooms=data.get("to_rooms"),
        to_kvm=data.get("to_kvm"),

        move_help=data.get("move_help"),
        move_date=move_date,
        move_time=data.get("move_time"),
        additional_info=data.get("additional_info"),

        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        phone=data.get("phone"),
        email=data.get("email"),
        consent=data.get("consent") == "true",
        created_at=timezone.now(),
    )


    # 🔍 Match businesses by city + move type
    city = (data.get("from_city") or "").strip().lower()
    move_type = (data.get("move_type") or "").strip().lower()
    today = date.today()
    matching_businesses = []

    if city and move_type:
        for b in Bedrift_info.objects.filter(active=True):
            business_cities = [c.strip().lower() for c in (b.cities or "").split(",")]
            business_move_types = [m.strip().lower() for m in (b.move_type or "").split(",")]

            if city not in business_cities or move_type not in business_move_types:
                continue

            # ✅ Check daily lead limit
            try:
                max_per_day = int(b.leads_per_day or 0)
            except ValueError:
                max_per_day = 0

            today_leads = JobDistribution.objects.filter(
                created_at__date=today
            ).filter(
                models.Q(business_1=b) | models.Q(business_2=b) | models.Q(business_3=b)
            ).count()

            if max_per_day == 0 or today_leads < max_per_day:
                matching_businesses.append(b)

    # 🎯 Randomly pick up to 3 businesses
    selected = random.sample(matching_businesses, k=min(3, len(matching_businesses)))

    # 💾 Save job distribution
    job_dist = JobDistribution.objects.create(
        inquiry=inquiry,
        business_1=selected[0] if len(selected) > 0 else None,
        business_2=selected[1] if len(selected) > 1 else None,
        business_3=selected[2] if len(selected) > 2 else None,
    )

    # 🔢 Increment total leads received
    for business in [job_dist.business_1, job_dist.business_2, job_dist.business_3]:
        if business:
            try:
                current_total = int(business.total_leads_received or 0)
            except ValueError:
                current_total = 0
            business.total_leads_received = str(current_total + 1)
            business.save(update_fields=["total_leads_received"])

    return JsonResponse({
        "success": True,
        "redirect_url": "/takk-for-din-foresporsel/"
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

        company = Bedrift_info.objects.create(
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

        return JsonResponse({
            "success": True,
            "redirect_url": f"/reg/fullfor/lag-bruker/?email={company.email}"
        })

    return render(request, "pages/about/for-business-partner.html")


def for_business(request):      
    return render(request, 'pages/about/for-business.html') 


def contact(request):      
    return render(request, 'pages/contact/contact.html')  

def about(request):      
    return render(request, 'pages/about/about.html')  
