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

