import re

from django import forms

from .models import MoveLead

# Spec §5.9: permissive, not RFC-strict — deliberately looser than Django's
# built-in EmailValidator so short/unusual-but-real addresses aren't rejected.
EPOST_PATTERN = re.compile(r"^\S+@\S+\.\S+$")
# Spec §5.9: digits, spaces, and a leading "+" only, at least 8 characters total.
TELEFON_PATTERN = re.compile(r"^[\d\s+]{8,}$")


class WizardForm(forms.Form):
    """
    Server-side re-implementation of every validation rule in
    kobly-full-site-spec.pdf §5.5-5.9. The client-side JS in wizard.js
    mirrors these rules only to enable/disable the "Neste" button — this
    form is the actual source of truth and must never be bypassed.
    """

    # --- Step 1: address ---
    fra = forms.CharField()
    fra_lat = forms.FloatField(required=False)
    fra_lon = forms.FloatField(required=False)
    til = forms.CharField()
    til_lat = forms.FloatField(required=False)
    til_lon = forms.FloatField(required=False)

    # --- Step 2: type & size ---
    flytte_type = forms.ChoiceField(choices=MoveLead.FLYTTE_TYPE_CHOICES)
    boligtype = forms.ChoiceField(choices=MoveLead.BOLIGTYPE_CHOICES)

    # --- Step 3: date ---
    flyttedato = forms.DateField(required=False)
    fleksibel = forms.BooleanField(required=False)

    # --- Step 4: goods (always optional) ---
    beskrivelse = forms.CharField(required=False, widget=forms.Textarea)

    # --- Step 5: contact ---
    navn = forms.CharField()
    telefon = forms.CharField()
    epost = forms.CharField()

    def clean_fra(self):
        value = self.cleaned_data["fra"].strip()
        if len(value) <= 2:
            raise forms.ValidationError("Fra-adresse må være minst 3 tegn.")
        return value

    def clean_til(self):
        value = self.cleaned_data["til"].strip()
        if len(value) <= 2:
            raise forms.ValidationError("Til-adresse må være minst 3 tegn.")
        return value

    def clean_navn(self):
        value = self.cleaned_data["navn"].strip()
        if len(value) <= 1:
            raise forms.ValidationError("Navn må være minst 2 tegn.")
        return value

    def clean_telefon(self):
        value = self.cleaned_data["telefon"].strip()
        if not TELEFON_PATTERN.match(value):
            raise forms.ValidationError("Ugyldig telefonnummer.")
        return value

    def clean_epost(self):
        value = self.cleaned_data["epost"].strip()
        if not EPOST_PATTERN.match(value):
            raise forms.ValidationError("Ugyldig e-postadresse.")
        return value

    def clean(self):
        cleaned = super().clean()
        # Spec §5.7: valid iff a date is set OR the user is flexible.
        if not cleaned.get("flyttedato") and not cleaned.get("fleksibel"):
            raise forms.ValidationError(
                "Velg en flyttedato eller merk av at du er fleksibel."
            )
        return cleaned
