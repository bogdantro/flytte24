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
    business = get_object_or_404(Bedrift_info, id=business_id)
    public_info = getattr(business, "public_info", None)
    
    return render(request, "core/public_business_profile.html", {
        "business": business,
        "public_info": public_info,
    })
