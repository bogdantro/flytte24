from django import forms
from .models import Flytteforesporsel

class FlytteforesporselForm(forms.ModelForm):
    class Meta:
        model = Flytteforesporsel
        fields = '__all__'
        exclude = ['created_at']


