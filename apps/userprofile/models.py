from django.contrib.auth.models import User
from django.db import models

class Userprofile(models.Model):
    user = models.OneToOneField(User, related_name='userprofile', on_delete=models.CASCADE)

    def __str__(self):
        return '%s' % self.user.username

User.userprofile = property(lambda u:Userprofile.objects.get_or_create(user=u)[0])





class Profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    profile_image = models.ImageField(blank=True, default='static/images/other/user-default.jpg', upload_to='static/other/users/')

    birth_date = models.CharField(blank=True, null=True, max_length=1000)    
    adress = models.CharField(blank=True, null=True, max_length=1000)    
    telefon = models.CharField(blank=True, null=True, max_length=1000)    
    stripe_id = models.CharField(blank=True, null=True, max_length=1000)    
    kyc_status = models.CharField(blank=True, null=True, max_length=1000)    

    def __str__(self):
        return f'Bruker - {self.user.username}'

