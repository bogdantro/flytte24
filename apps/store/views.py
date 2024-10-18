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
from .models import Membership

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def create_checkout_session(request):
    user = request.user
    customer_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

    try:
        customer = stripe.Customer.create(
            email=user.username,  # Use the user's email for the new customer
            name=customer_name
        )
        print("Customer created successfully:", customer.id)  # Log the customer ID for debugging
    except Exception as e:
        print("Error creating customer:", str(e))  # Catch any errors


    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_1Q7dVGCn41loPLwRN2BbOAYb',  # Replace with your Stripe Price ID
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri('/success/'),
        cancel_url=request.build_absolute_uri('/cancel/'),
        customer=customer.id
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



logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        # Verify the webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error("Invalid payload: %s", str(e))
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error("Invalid signature: %s", str(e))
        return HttpResponse(status=400)

    # Log the entire event for inspection
    logger.info("Received event: %s", json.dumps(event, indent=2))

    # Check the event type
    if event.get('type') == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        charge = payment_intent['charges']['data'][0]  # Get the first charge from the list
        
        # Extract customer email from billing details
        customer_email = charge['billing_details'].get('email')
        customer_id = payment_intent.get('customer')  # This will still be None unless a customer was created

        logger.info("Extracted customer_email: %s", customer_email)
        logger.info("Extracted customer_id: %s", customer_id)

        try:
            # Check if a User exists with the given email
            user = User.objects.get(username=customer_email)
            # If a user exists, create a membership
            Membership.objects.create(
                user=user,  # Assign the User instance here
                user_email=customer_email,
                stripe_customer_id=customer_id,
            )
        except User.DoesNotExist:
            logger.error("User with email %s does not exist.", customer_email)
            print("Could not create membership, user does not exist.")
        except Exception as e:
            logger.error("Could not create membership: %s", e)
            print("Could not create membership, error:", e)


    return HttpResponse(status=200)

def beome_member(request):
     # Get the language from the cookie, if available
    language = request.COOKIES.get('language')
    if language:
        translation.activate(language)
        request.LANGUAGE_CODE = language
    else:
        translation.activate('en')  # Default language if none is set
    return render(request, 'core/become-member.html')