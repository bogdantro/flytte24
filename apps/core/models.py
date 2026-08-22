from django.db import models
from django.contrib.auth.models import User

class Flytteforesporsel(models.Model):
    # Step 1 – Move Type
    move_type = models.CharField(max_length=100, blank=True, null=True)  

    # Step 2 – From/To Locations
    from_postcode = models.CharField(max_length=20, blank=True, null=True)
    from_city = models.CharField(max_length=100, blank=True, null=True)
    from_address = models.CharField(max_length=255, blank=True, null=True)
    from_property_type = models.CharField(max_length=50, blank=True, null=True)  # Hus / Leilighet
    from_rooms = models.CharField(max_length=50, blank=True, null=True)
    from_kvm = models.CharField(max_length=50, blank=True, null=True)  

    to_postcode = models.CharField(max_length=20, blank=True, null=True)
    to_city = models.CharField(max_length=100, blank=True, null=True)
    to_address = models.CharField(max_length=255, blank=True, null=True)
    to_property_type = models.CharField(max_length=50, blank=True, null=True)
    to_rooms = models.CharField(max_length=50, blank=True, null=True)
    to_kvm = models.CharField(max_length=50, blank=True, null=True)  

    # Step 3 – Move Details
    move_help = models.CharField(max_length=255, blank=True, null=True)
    move_date = models.DateField(blank=True, null=True) 
    move_time = models.CharField(max_length=100, blank=True, null=True)  

    # Step 4 – Contact Info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    consent = models.BooleanField(default=False)
    additional_info = models.TextField(blank=True, null=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.move_type})"


class Agency(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    logo = models.CharField(max_length=255, help_text="Static path, e.g. images/home/loeftlogo.svg")
    logo_blend_multiply = models.BooleanField(default=False)
    tagline = models.CharField(max_length=200)
    short = models.TextField()
    about = models.JSONField(default=list, help_text="List of paragraph strings")
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    review_count = models.PositiveIntegerField()
    jobs_completed = models.PositiveIntegerField()
    response_time = models.CharField(max_length=100)
    member_since = models.PositiveIntegerField()
    services = models.JSONField(default=list, help_text="List of strings")
    areas = models.JSONField(default=list, help_text="List of strings")
    contact_name = models.CharField(max_length=100)
    contact_role = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=50)
    reviews = models.JSONField(default=list, help_text="List of {name, date, stars, service, comment}")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Article(models.Model):
    slug = models.SlugField(max_length=200, unique=True)
    title = models.CharField(max_length=300)
    ingress = models.TextField()
    header_image = models.URLField(max_length=500, blank=True, default="")
    date = models.DateField()
    read_minutes = models.PositiveIntegerField()
    blocks = models.JSONField(default=list, help_text="List of {type, text} | {type:'list', items} | {type:'image', src, alt, caption} | {type:'cta'}")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.title

