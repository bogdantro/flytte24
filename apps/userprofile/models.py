from django.contrib.auth.models import User
from django.db import models

class Userprofile(models.Model):
    user = models.OneToOneField(User, related_name='userprofile', on_delete=models.CASCADE)

    def __str__(self):
        return '%s' % self.user.username

User.userprofile = property(lambda u:Userprofile.objects.get_or_create(user=u)[0])





class Profile(models.Model):
     
    MEDLEMSKAP = [
        ("Bruker", "Bruker"),
        ("Vanlig", "Vanlig"),
        ("Pro", "Pro"),
        ("Pro+", "Pro+"),
    ]
     
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    telefon = models.CharField(max_length=150, blank=True, null=True)
    medlemskap = models.CharField(max_length=150, choices=MEDLEMSKAP, blank=True, null=True)
    price = models.CharField(max_length=150, blank=True, null=True)
    org_nr = models.CharField(max_length=150, blank=True, null=True)
    profile_image = models.ImageField(blank=True, default='static/images/other/user-default.jpg', upload_to='static/other/users/')
    business_name = models.CharField(max_length=150, blank=True, null=True)
    last_subscription_change_date = models.DateField(null=True, blank=True)
    

    def __str__(self):
        if self.business_name:
            return f'Bedrift - {self.business_name}'
        else:
            return f'Bruker - {self.user.username}'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.user.username,
            'org_nr': self.org_nr,
            'business_name': self.business_name,
        }