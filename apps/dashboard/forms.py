from django import forms

from apps.pages.models import Page, PageSection


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ["title", "path", "status"]


class PageSectionForm(forms.ModelForm):
    class Meta:
        model = PageSection
        fields = ["heading", "subheading", "body_text", "button_label", "button_href", "image"]
