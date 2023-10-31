# forms.py
from django import forms
from ckeditor.fields import RichTextField  # Import RichTextField
from .models import Car  # Import your Car model

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['name', 'car_spesifikasjoner', 'car_brand', 'price', 'description']

    description = RichTextField()  # Use RichTextField for the description field
