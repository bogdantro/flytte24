from django.utils import timezone
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from datetime import timedelta



# models.py

from django.db import models
from django.contrib.auth.models import User

class Membership(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    user_email = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    payed = models.BooleanField(default=True)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username if self.user else self.user_email or "Membership (Assosicate the correct user)"
