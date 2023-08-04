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