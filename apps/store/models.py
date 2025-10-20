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


    # Leads information
    leads_per_day = models.CharField(max_length=90, blank=True, null=True)
    leads_per_week = models.CharField(max_length=90, blank=True, null=True)
    leads_per_month = models.CharField(max_length=90, blank=True, null=True)


    total_leads_received = models.CharField(max_length=90, blank=True, null=True)

    active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.company_name:
            return f"{self.company_name} ({self.email})"
        return f"{self.email}"



class PublicBusinessInformation(models.Model):
    business = models.OneToOneField(
        Bedrift_info,
        on_delete=models.CASCADE,
        related_name="public_info"
    )
    logo = models.ImageField(upload_to="business_logos/", blank=True, null=True)
    about_us = models.TextField(blank=True, null=True)
    faq = models.TextField(blank=True, null=True, help_text="Use line breaks to separate questions/answers.")
    
    def __str__(self):
        return f"Public info for {self.business.company_name}"


from django.core.exceptions import ValidationError

class BusinessImage(models.Model):
    public_info = models.ForeignKey(
        "PublicBusinessInformation",
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="business_images/")

    def clean(self):
        if self.public_info.images.count() >= 6 and not self.pk:
            raise ValidationError("Du kan maksimalt laste opp 6 bilder.")

    def __str__(self):
        return f"Image for {self.public_info.business.company_name}"



class Review(models.Model):
    business = models.ForeignKey(
        Bedrift_info,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    name = models.CharField(max_length=100)
    rating = models.PositiveIntegerField(default=5, choices=[(i, f"{i} ⭐") for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rating}⭐ by {self.name} for {self.business.company_name}"


class JobDistribution(models.Model):
    inquiry = models.ForeignKey(
        "core.Flytteforesporsel",
        on_delete=models.CASCADE,
        related_name="distributions"
    )

    # 🧩 Three business slots
    business_1 = models.ForeignKey(
        "store.Bedrift_info",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="distribution_primary",
        verbose_name="Business 1"
    )
    business_2 = models.ForeignKey(
        "store.Bedrift_info",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="distribution_secondary",
        verbose_name="Business 2"
    )
    business_3 = models.ForeignKey(
        "store.Bedrift_info",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="distribution_tertiary",
        verbose_name="Business 3"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    viewed = models.BooleanField(default=False)

    def __str__(self):
        names = [b.company_name for b in [self.business_1, self.business_2, self.business_3] if b]
        return f"Distribution for {self.inquiry} → {', '.join(names)}"

    def businesses(self):
        """Convenience list of the businesses assigned here."""
        return [b for b in [self.business_1, self.business_2, self.business_3] if b]
