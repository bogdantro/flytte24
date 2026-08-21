from django.conf import settings
from django.db import models


class Page(models.Model):
    """
    One real page on the public site (e.g. the home page). A Page with no
    matching PageSection rows, or no Page row at all for a given
    template_key, is not an error — every core view falls back to that
    page's hardcoded template copy (see apps/core/views.py `home`).
    """

    TEMPLATE_KEY_CHOICES = [
        ("home", "Forside"),
        ("about", "Om oss"),
        ("for_business", "For bedrifter"),
        ("contact", "Kontakt"),
    ]
    STATUS_CHOICES = [
        ("draft", "Utkast"),
        ("published", "Publisert"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    path = models.CharField(max_length=200, unique=True, help_text="Ekte URL, f.eks. /om-oss/")
    template_key = models.CharField(max_length=50, choices=TEMPLATE_KEY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class PageSection(models.Model):
    """
    One editable block within a Page. Fixed, known section_type set —
    see docs/superpowers/specs/2026-08-21-dashboard-cms-and-business-admin-design.md
    for the "why no generic block builder" decision. extra_json holds
    list-shaped content (FAQ pairs, testimonial cards, step cards, city
    cards) that doesn't fit the flat typed fields.
    """

    SECTION_TYPE_CHOICES = [
        ("hero", "Hero"),
        ("image_strip", "Bildestripe"),
        ("stats", "Statistikk"),
        ("services", "Tjenester"),
        ("testimonials", "Kundeuttalelser"),
        ("faq", "Ofte stilte spørsmål"),
        ("how_it_works", "Slik fungerer det"),
        ("trust", "Tillit"),
        ("cta", "Call-to-action"),
        ("footer", "Footer"),
        ("generic_text", "Generisk tekst"),
    ]

    page = models.ForeignKey(Page, related_name="sections", on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    section_type = models.CharField(max_length=30, choices=SECTION_TYPE_CHOICES)
    heading = models.CharField(max_length=300, blank=True, default="")
    subheading = models.CharField(max_length=500, blank=True, default="")
    body_text = models.TextField(blank=True, default="")
    button_label = models.CharField(max_length=100, blank=True, default="")
    button_href = models.CharField(max_length=300, blank=True, default="")
    image = models.ImageField(upload_to="pages/", blank=True, null=True)
    extra_json = models.JSONField(blank=True, default=dict)

    class Meta:
        ordering = ["page", "order"]

    def __str__(self):
        return f"{self.page.title} — {self.get_section_type_display()}"
