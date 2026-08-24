import re

from django import forms
from .models import Flytteforesporsel

class FlytteforesporselForm(forms.ModelForm):
    class Meta:
        model = Flytteforesporsel
        fields = '__all__'
        exclude = ['created_at']


# Spec vocabulary for /for-bedrifter/bli-partner/ (kept as module-level tuples,
# not sourced from apps.store.models.Bedrift_info, since move_type/cities are
# comma-separated free text on that model — this is the one place their
# allowed values are enumerated). Same 4-digit rule as everywhere else on the
# site that collects a Norwegian postal code.
MOVE_TYPE_CHOICES = [
    (v, v) for v in [
        "Flyttehjelp", "Pakking", "Flyttevask", "Lagring",
        "Montering", "Kontorflytting", "Utlandsflytting", "Dødsbo",
    ]
]
CITY_CHOICES = [
    (v, v) for v in ["Oslo", "Bergen", "Trondheim", "Stavanger", "Tromsø"]
]
POSTNUMMER_PATTERN = re.compile(r"^\d{4}$")


class PartnerWizardForm(forms.Form):
    """
    Server-side validation for the 4-step business-signup wizard at
    /for-bedrifter/bli-partner/. A plain Form (not a ModelForm against
    Bedrift_info) since move_type/cities arrive as lists here and are only
    joined into that model's comma-separated CharFields on save — see
    apps.core.views.for_business_partner. Error message style mirrors
    apps.leads.forms.WizardForm (clean_* methods, Norwegian messages).
    """

    # --- Step 1: services ---
    move_type = forms.MultipleChoiceField(
        choices=MOVE_TYPE_CHOICES,
        error_messages={"required": "Velg minst én tjeneste."},
    )

    # --- Step 2: cities covered ---
    cities = forms.MultipleChoiceField(
        choices=CITY_CHOICES,
        error_messages={"required": "Velg minst én by."},
    )

    # --- Step 3: about the company ---
    company_name = forms.CharField(error_messages={"required": "Firmanavn er påkrevd."})
    company_number = forms.CharField(required=False)
    employees = forms.CharField(required=False)
    website = forms.CharField(required=False)
    address = forms.CharField(error_messages={"required": "Adresse er påkrevd."})
    postal_code = forms.CharField(error_messages={"required": "Postnummer er påkrevd."})
    city = forms.CharField(error_messages={"required": "By er påkrevd."})

    # --- Step 4: contact person + logo ---
    tiltaleform = forms.CharField(required=False)
    first_name = forms.CharField(error_messages={"required": "Fornavn er påkrevd."})
    last_name = forms.CharField(error_messages={"required": "Etternavn er påkrevd."})
    email = forms.EmailField(error_messages={
        "required": "E-post er påkrevd.",
        "invalid": "Ugyldig e-postadresse.",
    })
    phone = forms.CharField(error_messages={"required": "Telefon er påkrevd."})
    logo = forms.ImageField(required=False)

    def clean_postal_code(self):
        value = self.cleaned_data["postal_code"].strip()
        if not POSTNUMMER_PATTERN.match(value):
            raise forms.ValidationError("Postnummer må bestå av 4 siffer.")
        return value


