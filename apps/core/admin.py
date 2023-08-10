from django.contrib import admin
from .models import *
from django.utils import timezone
from django.db.models import Sum

admin.site.register(Contact)
admin.site.register(Verdivurdering)
admin.site.register(Location)
admin.site.register(Booking)
admin.site.register(UnBook)