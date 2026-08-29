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
    """The "E-post" field on core/signup.html is bound to `username` (login
    is by email address), but User.email was previously never populated at
    all — nothing (password reset, notifications) could ever rely on it.
    save() now mirrors the submitted username into email too."""

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'input'
        self.fields['password1'].widget.attrs['class'] = 'input'
        self.fields['password2'].widget.attrs['class'] = 'input'

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['username']
        if commit:
            user.save()
        return user





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
from apps.store.models import Bedrift_info, PublicBusinessInformation, BusinessImage


class BusinessSelfEditForm(forms.ModelForm):
    """Core business info a partner can edit about themselves — the
    account-side equivalent of apps.dashboard.forms.BusinessCoreForm.
    Deliberately excludes: `email` (also their login username; changing it
    would need its own re-verification flow, out of scope here — contact
    staff to change it), `active`/`total_leads_received` (system-managed),
    `priority_score`/`tags`/`internal_notes` (staff-only, the model's own
    docstring says internal_notes/tags are "never shown on the business's
    own... account pages"), and `leads_per_day/week/month` (edited from the
    leads page instead — apps.userprofile.views.foresporsel_database)."""

    class Meta:
        model = Bedrift_info
        fields = [
            "company_name", "company_number", "employees", "phone", "website",
            "address", "postal_code", "city", "tiltaleform", "first_name", "last_name",
            "cities", "move_type",
        ]
        widgets = {
            "cities": forms.TextInput(attrs={"placeholder": "Oslo, Bergen, Trondheim"}),
            "move_type": forms.TextInput(attrs={"placeholder": "Flyttehjelp, Pakking"}),
        }


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
