import json

from django import forms

from apps.core.models import Article
from apps.store.models import Bedrift_info, PublicBusinessInformation

ARTICLE_BLOCK_TYPES = {"h2", "p", "list", "image", "cta"}


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


class ArticleForm(forms.ModelForm):
    """Blog article editor. `blocks` (the article body — a list of typed
    {type, ...} dicts, see apps.core.models.Article's own field help_text)
    is edited as raw JSON rather than a per-block-type visual editor — a
    real block-by-block builder is a much bigger feature (add/remove/
    reorder h2/p/list/image/cta blocks individually); this is the pragmatic
    version that makes an article's content actually editable from the
    dashboard at all, which previously had no path except the
    seed_marketing_content management command."""

    blocks_json = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 16, "class": "dashboard-form__textarea-mono"}),
        required=True,
        label="Innhold (JSON)",
        help_text=(
            'Liste med blokker. Typer: {"type": "h2", "text": "..."}, '
            '{"type": "p", "text": "..."}, {"type": "list", "items": ["...", "..."]}, '
            '{"type": "image", "src": "...", "alt": "...", "caption": "..."} (caption valgfri), '
            '{"type": "cta"}.'
        ),
    )

    class Meta:
        model = Article
        fields = ["title", "slug", "ingress", "header_image", "date", "read_minutes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "ingress": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["blocks_json"].initial = json.dumps(self.instance.blocks, ensure_ascii=False, indent=2)

    def clean_blocks_json(self):
        raw = self.cleaned_data["blocks_json"]
        try:
            blocks = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Ugyldig JSON: {exc}")
        if not isinstance(blocks, list):
            raise forms.ValidationError("Innholdet må være en liste med blokker.")
        for i, block in enumerate(blocks, start=1):
            if not isinstance(block, dict) or "type" not in block:
                raise forms.ValidationError(f"Blokk {i} mangler \"type\".")
            if block["type"] not in ARTICLE_BLOCK_TYPES:
                raise forms.ValidationError(f"Blokk {i} har ukjent type \"{block['type']}\".")
        return blocks

    def save(self, commit=True):
        article = super().save(commit=False)
        article.blocks = self.cleaned_data["blocks_json"]
        if commit:
            article.save()
        return article
