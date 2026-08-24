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

def _page_context(request, page):
    """Shared by home() and render_page() — every view that renders a
    Page/PageSection-backed template builds its context this way, so
    duplicated pages (or any future non-home Page using this same
    template) render identically to the original."""
    from django.middleware.csrf import get_token

    sections = {s.section_type: s for s in page.sections.all()} if page else {}
    # Staff editing a page has no <form> on this page to trigger Django's
    # normal csrftoken-cookie-on-render behavior — force it so inline-edit.js
    # has a token to read before the user's first edit.
    is_editable = bool(page) and request.user.is_authenticated and request.user.is_staff
    if is_editable:
        get_token(request)
    return {"page": page, "sections": sections, "is_editable": is_editable}


def home(request):
    from apps.pages.models import Page

    page = Page.objects.filter(template_key="home", status="published").first()
    return render(request, 'core/home.html', _page_context(request, page))


def render_page(request, page_path):
    """Catch-all for any Page at a path other than "/" (e.g. a duplicated
    page) — see demo/urls.py, where this is the last pattern tried. Draft
    pages are visible to staff only (so a freshly duplicated page can be
    previewed and edited before publishing) — everyone else 404s on a
    draft exactly as if the page didn't exist. Only template_key="home"
    has a section-based template today (the others still render fully
    hardcoded — see apps/pages's design spec), so a Page using any other
    template_key 404s here rather than silently rendering the wrong
    markup."""
    from apps.pages.models import Page

    path = "/" + page_path.rstrip("/") + "/"
    page = Page.objects.filter(path=path).first()
    is_staff = request.user.is_authenticated and request.user.is_staff
    if not page or page.template_key != "home" or (page.status != "published" and not is_staff):
        raise Http404("Ingen side på denne stien.")
    return render(request, 'core/home.html', _page_context(request, page))


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



import requests

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

    # 🌐 Define separate webhook URLs for businesses
    webhook_url_1 = "https://hooks.zapier.com/hooks/catch/16531899/uri7mol/"
    webhook_url_2 = "https://hooks.zapier.com/hooks/catch/16531899/urs5di1/"
    webhook_url_3 = "https://hooks.zapier.com/hooks/catch/16531899/urs5mfe/"

    webhook_urls = [webhook_url_1, webhook_url_2, webhook_url_3]

    # 📨 Send individual payloads to each business
    for idx, b in enumerate(selected):
        payload = {
            "inquiry": {
                "id": inquiry.id,
                "move_type": inquiry.move_type,
                "from_city": inquiry.from_city,
                "to_city": inquiry.to_city,
                "move_date": inquiry.move_date.isoformat() if inquiry.move_date else None,
                "move_time": inquiry.move_time,
                "first_name": inquiry.first_name,
                "last_name": inquiry.last_name,
                "phone": inquiry.phone,
                "email": inquiry.email,
                "additional_info": inquiry.additional_info,
            },
            "business": {
                "id": b.id,
                "company_name": b.company_name,
                "email": b.email,
                "phone": b.phone,
                "website": b.website,
                "address": b.address,
                "postal_code": b.postal_code,
                "city": b.city,
                "first_name": b.first_name,
                "last_name": b.last_name,
            },
            "webhook_number": idx + 1,
        }

        try:
            resp = requests.post(webhook_urls[idx], json=payload, timeout=8)
            resp.raise_for_status()
            print(f"✅ Sent webhook #{idx + 1} to {b.company_name}")
        except requests.RequestException as e:
            print(f"⚠️ Webhook #{idx + 1} failed for {b.company_name}: {e}")

    # 📩 Send webhook to customer with full lead + all matched businesses
    customer_webhook_url = "https://hooks.zapier.com/hooks/catch/16531899/urs5514/"  # bytt til riktig URL

    customer_payload = {
        "inquiry": {
            "id": inquiry.id,
            "move_type": inquiry.move_type,
            "from_postcode": inquiry.from_postcode,
            "from_city": inquiry.from_city,
            "from_address": inquiry.from_address,
            "from_property_type": inquiry.from_property_type,
            "from_rooms": inquiry.from_rooms,
            "from_kvm": inquiry.from_kvm,
            "to_postcode": inquiry.to_postcode,
            "to_city": inquiry.to_city,
            "to_address": inquiry.to_address,
            "to_property_type": inquiry.to_property_type,
            "to_rooms": inquiry.to_rooms,
            "to_kvm": inquiry.to_kvm,
            "move_help": inquiry.move_help,
            "move_date": inquiry.move_date.isoformat() if inquiry.move_date else None,
            "move_time": inquiry.move_time,
            "additional_info": inquiry.additional_info,
            "first_name": inquiry.first_name,
            "last_name": inquiry.last_name,
            "phone": inquiry.phone,
            "email": inquiry.email,
        },
        "matched_businesses": [
            {
                "id": b.id,
                "company_name": b.company_name,
                "email": b.email,
                "phone": b.phone,
                "website": b.website,
                "address": b.address,
                "postal_code": b.postal_code,
                "city": b.city,
                "first_name": b.first_name,
                "last_name": b.last_name,
            }
            for b in selected
        ]
    }

    try:
        resp = requests.post(customer_webhook_url, json=customer_payload, timeout=8)
        resp.raise_for_status()
        print(f"✅ Sent webhook to customer at {customer_webhook_url}")
    except requests.RequestException as e:
        print(f"⚠️ Customer webhook failed: {e}")

    return JsonResponse({
        "success": True,
        "redirect_url": f"/takk-for-din-foresporsel/{inquiry.id}/"
    })

from django.shortcuts import render, get_object_or_404

from django.shortcuts import render, get_object_or_404

def takk_for_foresporsel(request, inquiry_id=None):
    """Viser takk-side med liste over bedrifter som mottok leaden"""
    inquiry = get_object_or_404(Flytteforesporsel, id=inquiry_id)
    job_dist = JobDistribution.objects.filter(inquiry=inquiry).first()

    businesses = []
    if job_dist:
        for b in [job_dist.business_1, job_dist.business_2, job_dist.business_3]:
            if b:
                businesses.append(b)

    return render(request, "core/takk_for_foresporsel.html", {
        "inquiry": inquiry,
        "businesses": businesses,
    })


def for_business(request):      
    return render(request, 'pages/about/for-business.html') 



from apps.store.models import PublicBusinessInformation
from .forms import PartnerWizardForm


def for_business_partner(request):
    """
    Renders the 4-step business-signup wizard (GET) and processes the final
    submission (POST) — a real form POST + 302 redirect, mirroring
    apps.leads.views.wizard's own pattern (not the JSON/AJAX response this
    view used to return, which no JS on the page ever called).

    POST: validates via PartnerWizardForm; on success creates the
    Bedrift_info row (move_type/cities joined from the validated list
    fields) and a linked PublicBusinessInformation row (logo, if uploaded),
    then redirects to the account-creation step of the signup flow. On
    invalid input, re-renders the same template with the bound form so
    entered values and errors persist.
    """
    if request.method == "POST":
        form = PartnerWizardForm(request.POST, request.FILES)
        if form.is_valid():
            company = Bedrift_info.objects.create(
                move_type=", ".join(form.cleaned_data["move_type"]),
                cities=", ".join(form.cleaned_data["cities"]),
                company_name=form.cleaned_data["company_name"],
                company_number=form.cleaned_data["company_number"],
                employees=form.cleaned_data["employees"],
                email=form.cleaned_data["email"],
                phone=form.cleaned_data["phone"],
                website=form.cleaned_data["website"],
                address=form.cleaned_data["address"],
                postal_code=form.cleaned_data["postal_code"],
                city=form.cleaned_data["city"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
            )
            PublicBusinessInformation.objects.create(
                business=company,
                logo=form.cleaned_data["logo"],
            )
            return redirect(f"/reg/fullfor/lag-bruker/?email={company.email}")
        # Invalid: fall through and re-render with errors attached (only
        # reachable if a client bypasses partner-wizard.js's own validation).
    else:
        form = PartnerWizardForm()

    return render(request, "pages/about/for-business-partner.html", {"form": form})


def for_business(request):      
    return render(request, 'pages/about/for-business.html') 


def contact(request):      
    return render(request, 'pages/contact/contact.html')  

def about(request):
    return render(request, 'pages/about/about.html')


def blog_index(request):
    from apps.core.models import Article
    articles = Article.objects.all()
    return render(request, "pages/blog/index.html", {"articles": articles})


def blog_article(request, slug):
    from apps.core.models import Article
    article = get_object_or_404(Article, slug=slug)
    return render(request, "pages/blog/article.html", {"article": article})


def agency_list(request):
    from apps.core.models import Agency
    agencies = Agency.objects.all()
    return render(request, "pages/agencies/list.html", {"agencies": agencies})


def agency_detail(request, slug):
    from apps.core.models import Agency
    agency = get_object_or_404(Agency, slug=slug)
    return render(request, "pages/agencies/detail.html", {"agency": agency})  
