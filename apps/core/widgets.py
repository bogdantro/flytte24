# bookings/widgets.py
from django import forms

class CustomDatePicker(forms.DateInput):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs']['class'] = 'datepicker'
        return context
