import datetime
from django.db import models
from datetime import date
from django.contrib.auth.models import User
from django.utils import tree
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(blank=True, null=True, default='static/images/default.png', upload_to='static/images/other/user_images/')

    def __str__(self):
        return f'{self.user.username} sin profil'


class Contact(models.Model):
    name = models.CharField(max_length=400, blank=False)
    email = models.EmailField(max_length=100, blank=False)
    message = models.TextField(blank=False)
    is_answered = models.BooleanField(default=False)

    def __str__(self):
        return self.name  

class Verdivurdering(models.Model):
    reg_nr = models.CharField(max_length=200)
    km = models.CharField(max_length=200)
    name = models.CharField(max_length=400, blank=False)
    email = models.EmailField(max_length=100, blank=False)
    telefon = models.CharField(max_length=100, blank=False)
    vilkaar = models.BooleanField(default=False)
    is_answered = models.BooleanField(default=False)

    def __str__(self):
        return self.name  



class Location(models.Model):
    cords1 = models.CharField(max_length=150, blank=True)
    cords2 = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f'{self.cords1}, {self.cords2}'
    

class Booking(models.Model):
    user = models.ForeignKey(User, related_name='bookings', on_delete=models.SET_NULL, blank=True, null=True)
    date = models.CharField(max_length=100, blank=True, null=True)
    time = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    preference = models.CharField(max_length=100, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100 ,blank=True, null=True)
    mobile_number = models.CharField(max_length=100, blank=True, null=True)
    reg_number = models.CharField(max_length=100, blank=True, null=True)
    km = models.CharField(max_length=100 ,blank=True, null=True)
    car_name_model = models.CharField(max_length=100, blank=True, null=True)
    sms_reminder = models.BooleanField(default=False,blank=True, null=True)
    car_younger_than_10 = models.BooleanField(default=False,blank=True, null=True)
    less_than_150000km = models.BooleanField(default=False,blank=True, null=True)
    vilkaar = models.BooleanField(default=False,blank=True, null=True)
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.date} {self.time}"


class UnBook(models.Model):
    full_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True)
    message = models.TextField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.email}"
