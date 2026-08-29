import requests
import stripe
import logging
import json

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
from django.http import HttpResponse
from django.utils import translation
# views.py

from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import *



from django.shortcuts import render, get_object_or_404
from apps.store.models import Bedrift_info, PublicBusinessInformation

def public_business_profile(request, business_id):
    """Customer-facing profile — what the wizard-matched businesses look
    like from the outside. Inactive businesses (not yet approved, or
    deactivated) still resolve so a business can preview their own profile
    from myaccount, but only for staff or that business's own logged-in
    user — the template's own "bare du og Kobly kan se denne
    forhåndsvisningen" (only you and Kobly can see this preview) claim was
    previously unenforced, so anyone who guessed/enumerated a business_id
    could view an unapproved business's full profile."""
    business = get_object_or_404(Bedrift_info, id=business_id)
    if not business.active:
        is_owner = request.user.is_authenticated and getattr(business, "user_id", None) == request.user.id
        if not (request.user.is_authenticated and request.user.is_staff) and not is_owner:
            raise Http404
    public_info = getattr(business, "public_info", None)
    reviews = business.reviews.all().order_by("-created_at")
    average_rating = reviews.aggregate(Avg("rating"))["rating__avg"]

    # move_type/cities are comma-separated free text (see
    # apps.core.forms.MOVE_TYPE_CHOICES — already human-readable values
    # like "Flyttehjelp", not slugs needing a label lookup).
    cities = [c.strip() for c in (business.cities or "").split(",") if c.strip()]
    move_types = [m.strip() for m in (business.move_type or "").split(",") if m.strip()]

    return render(request, "core/public_business_profile.html", {
        "business": business,
        "public_info": public_info,
        "reviews": reviews,
        "average_rating": average_rating,
        "cities": cities,
        "move_types": move_types,
        "images": public_info.images.all() if public_info else [],
    })
