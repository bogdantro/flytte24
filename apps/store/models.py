from django.db import models
from django.contrib.auth.models import User
from apps.core.models import *

class Bedrift_info(models.Model):
    # Relation to User (linked after signup)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name="bedrift_info")

    # Step 1
    move_type = models.CharField(max_length=255, blank=True, null=True)  # comma-separated

    # Step 2
    cities = models.CharField(max_length=255, blank=True, null=True)  # comma-separated

    # Step 3
    company_name = models.CharField(max_length=255)
    company_number = models.CharField(max_length=50, blank=True, null=True)
    employees = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    website = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)

    # Step 4
    tiltaleform = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.company_name:
            return f"{self.company_name} ({self.email})"
        return f"{self.email}"




class JobDistribution(models.Model):
    business = models.ForeignKey(Bedrift_info, on_delete=models.CASCADE, related_name="received_jobs")
    inquiry = models.ForeignKey("core.Flytteforesporsel", on_delete=models.CASCADE, related_name="distributed_to")
    created_at = models.DateTimeField(auto_now_add=True)
    viewed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.business.company_name} ← {self.inquiry.from_city}"
