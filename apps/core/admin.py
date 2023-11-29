from django.contrib import admin
from .models import *
from django.utils import timezone
from django.db.models import Sum


class VerdivurderingAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'reg_nr', 'km', 'is_answered']

admin.site.register(Verdivurdering, VerdivurderingAdmin)

class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'date', 'time', 'location', 'preference', 'reg_number', 'is_booked', 'fakturert']
    list_editable = ('is_booked', 'fakturert')

admin.site.register(Booking, BookingAdmin)


admin.site.register(UnBook)
admin.site.register(Visning)