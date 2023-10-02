from django.contrib.auth.models import User
from django.db import models

class Userprofile(models.Model):
    user = models.OneToOneField(User, related_name='userprofile', on_delete=models.CASCADE)

    def __str__(self):
        return '%s' % self.user.username

User.userprofile = property(lambda u:Userprofile.objects.get_or_create(user=u)[0])


