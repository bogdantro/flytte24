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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username
