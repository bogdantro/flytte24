from django import forms
from django.contrib.auth.forms import *
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .models import Userprofile
from apps.core.models import Profile
from apps.store.models import *

from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox


class UserprofileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserprofileForm, self).__init__(*args, **kwargs)


    class Meta:
        model = Userprofile
        fields = '__all__'
        exclude = ('user',)

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(max_length=255, required=True)

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'input'
        self.fields['email'].widget.attrs['class'] = 'input'
        self.fields['password1'].widget.attrs['class'] = 'input'
        self.fields['password2'].widget.attrs['class'] = 'input'
        self.fields['first_name'].widget.attrs['class'] = 'input'
        self.fields['last_name'].widget.attrs['class'] = 'input'

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']



class PasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)

    # captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

class SetPasswordForm(SetPasswordForm):
    class Meta:
        model = get_user_model()
        fields = ['new_password1', 'new_password2']

class AcceptBidForm(forms.Form):
    pass     




class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['telefon']
