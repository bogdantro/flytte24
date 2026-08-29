from django import forms

from apps.store.models import Bedrift_info, PublicBusinessInformation


class BusinessCoreForm(forms.ModelForm):
    """Everything editable on Bedrift_info except `active` (its own
    dedicated toggle endpoint) and `total_leads_received` (a
    system-incremented counter, read-only here)."""

    class Meta:
        model = Bedrift_info
        fields = [
            "company_name", "company_number", "email", "phone", "website",
            "address", "postal_code", "city", "tiltaleform", "first_name", "last_name",
            "cities", "move_type",
            "leads_per_day", "leads_per_week", "leads_per_month", "priority_score",
            "tags", "internal_notes",
        ]


class BusinessPublicInfoForm(forms.ModelForm):
    class Meta:
        model = PublicBusinessInformation
        fields = ["logo", "about_us", "faq"]
