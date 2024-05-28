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


# views.py

import stripe
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import Membership

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def create_checkout_session(request):
    user = request.user
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_1Ot84XCn41loPLwR08ulwP0Y',  # Replace with your Stripe Price ID
            'quantity': 1,
        }],
        mode='subscription',
        success_url=request.build_absolute_uri('/success/'),
        cancel_url=request.build_absolute_uri('/cancel/'),
        customer_email=user.email,
    )
    return redirect(session.url, code=303)



def success(request):
    return render(request, 'core/sucess.html')

def cancel(request):
    return render(request, 'core/error.html')
# views.py

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Membership

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    if event['type'] == 'invoice.payment_succeeded':
        customer_id = event['data']['object']['customer']
        membership = Membership.objects.get(stripe_customer_id=customer_id)
        membership.active = True
        membership.save()
    elif event['type'] == 'invoice.payment_failed':
        customer_id = event['data']['object']['customer']
        membership = Membership.objects.get(stripe_customer_id=customer_id)
        membership.active = False
        membership.save()

    return HttpResponse(status=200)


def beome_member(request):
    return render(request, 'core/become-member.html')