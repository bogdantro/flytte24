import re

from django import forms

from .models import Flytteforesporsel
from apps.store.models import Bedrift_info, phone_validator

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
        "Montering", "Kontorflytting", "Distansflytting", "Dødsbo",
    ]
]
CITY_CHOICES = [
    (v, v) for v in ["Oslo", "Bergen", "Trondheim", "Stavanger", "Tromsø"]
]
POSTNUMMER_PATTERN = re.compile(r"^\d{4}$")


class PartnerWizardForm(forms.Form):
    """
    Server-side validation for the 2-step business-signup wizard at
    /for-bedrifter/bli-partner/ ("Om bedriften", then "Kontaktperson og
    logo"). A plain Form (not a ModelForm against Bedrift_info) since
    move_type/cities may arrive as lists here and are only joined into that
    model's comma-separated CharFields on save — see
    apps.core.views.for_business_partner. Error message style mirrors
    apps.leads.forms.WizardForm (clean_* methods, Norwegian messages).
    """

    # --- Services / cities covered ---
    # No longer collected in the wizard itself (steps 1 & 2 were removed —
    # the wizard now opens straight on "Om bedriften"). A partner sets their
    # coverage right after signing up, from the "Dekning" section of the
    # account portal (apps.userprofile.views.update_business_coverage), and
    # staff can set it on the dashboard business page. Kept as optional
    # fields here only so a hand-crafted POST that still sends them keeps
    # working.
    move_type = forms.MultipleChoiceField(choices=MOVE_TYPE_CHOICES, required=False)
    cities = forms.MultipleChoiceField(choices=CITY_CHOICES, required=False)

    # --- Step 1: about the company ---
    company_name = forms.CharField(error_messages={"required": "Firmanavn er påkrevd."})
    company_number = forms.CharField(required=False)
    employees = forms.CharField(required=False)
    website = forms.CharField(required=False)
    address = forms.CharField(error_messages={"required": "Adresse er påkrevd."})
    postal_code = forms.CharField(error_messages={"required": "Postnummer er påkrevd."})
    city = forms.CharField(error_messages={"required": "By er påkrevd."})

    # --- Step 4: contact person + logo ---
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

    def clean_phone(self):
        # Same pattern as Bedrift_info.phone's own model-level validator
        # (apps.store.models.phone_validator) — checked here too since
        # apps.core.views.for_business_partner saves via
        # Bedrift_info.objects.create(**cleaned_data) directly rather than
        # form.save()/full_clean(), so the model validator alone would
        # never actually run.
        value = self.cleaned_data["phone"].strip()
        phone_validator(value)
        return value

    def clean_logo(self):
        # apps.core.views.for_business_partner creates PublicBusinessInformation
        # directly (Model.objects.create(...)) rather than via a ModelForm, so
        # PublicBusinessInformation.logo's own model-level validate_max_file_size
        # validator (apps.store.models) never runs for this one upload path —
        # check it here too.
        from apps.store.models import validate_max_file_size
        value = self.cleaned_data.get("logo")
        if value:
            validate_max_file_size(value)
        return value

    def clean_email(self):
        # Bedrift_info.email is unique at the DB level — checked here too
        # so a duplicate submission (e.g. a double-click before the wizard's
        # own submit-button-disable JS kicks in) surfaces as a normal form
        # error instead of an IntegrityError, and so it can never silently
        # create a second row for the same company that a later signup
        # would then have to guess between.
        value = self.cleaned_data["email"].strip()
        if Bedrift_info.objects.filter(email__iexact=value).exists():
            raise forms.ValidationError("Det finnes allerede en søknad med denne e-postadressen.")
        return value


