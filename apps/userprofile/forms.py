from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import *

from .models import *
from django.contrib.auth import get_user_model

class UserprofileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserprofileForm, self).__init__(*args, **kwargs)


    class Meta:
        model = Userprofile
        fields = '__all__'
        exclude = ('user',)

class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'input'
        self.fields['password1'].widget.attrs['class'] = 'input'
        self.fields['password2'].widget.attrs['class'] = 'input'

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password1', 'password2']





class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']





class ChangeSubscriptionForm(forms.Form):
    MEDLEMSKAP_CHOICES = [
        ("Bruker", "Bruker"),
        ("Vanlig", "Vanlig"),
        ("Pro", "Pro"),
        ("Pro+", "Pro+"),
    ]

    new_subscription = forms.ChoiceField(choices=MEDLEMSKAP_CHOICES, label='New Subscription')

    def clean_new_subscription(self):
        new_subscription = self.cleaned_data['new_subscription']

        # Add any additional validation if needed

        return new_subscription
    


class SetPasswordForm(SetPasswordForm):
    class Meta:
        model = get_user_model()
        fields = ['new_password1', 'new_password2']    





from django import forms
from apps.store.models import PublicBusinessInformation, BusinessImage

class PublicBusinessInformationForm(forms.ModelForm):
    class Meta:
        model = PublicBusinessInformation
        fields = ["logo", "about_us", "faq"]
        widgets = {
            "about_us": forms.Textarea(attrs={"rows": 5, "placeholder": "Skriv litt om bedriften din..."}),
            "faq": forms.Textarea(attrs={"rows": 5, "placeholder": "Legg til ofte stilte spørsmål..."}),
        }

class BusinessImageForm(forms.ModelForm):
    class Meta:
        model = BusinessImage
        fields = ["image"]
