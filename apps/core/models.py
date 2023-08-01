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



class Booking(models.Model):
    date = models.DateField()
    location = models.CharField(max_length=1000)
    helper = models.CharField(max_length=1000)

    def __str__(self):
        return self.date