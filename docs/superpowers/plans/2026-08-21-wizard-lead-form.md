# Kobly Wizard Lead Form (/wizard) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `/wizard` 5-step lead-capture form end-to-end in Django — the single highest-priority page on the Kobly site, per `kobly-full-site-spec.pdf` §1/§16 — with real server-side validation, a `MoveLead`/`LeadImage` database backend, and a working submit → save → receipt-email flow. This is Phase 1 of the full-site rebuild; marketing pages (home, city, agency, blog, partner) are a later phase.

**Architecture:** New Django app `apps/leads`. One route (`/wizard/`) renders a single HTML page containing all 5 steps; a small vanilla-JS controller (no framework) shows/hides steps and drives the 260ms slide/fade transitions client-side (Option A from spec §16.3, chosen for UX fidelity to the reference). A single native `<form method="post" enctype="multipart/form-data">` wraps all 5 steps and is submitted once, on step 5. The DOM inputs themselves are the source of truth for form state (no JS shadow-state object for text/choice fields) — JS only tracks the current step index/direction, the selected-photos array (browsers require this for multi-file "append" UX), and the Leaflet map instances. Django's `WizardForm` re-validates everything server-side using the exact rules from spec §5.5–5.9; client-side checks only gate the "Neste" button and are never trusted as the source of truth.

**Tech Stack:** Django 5.1 (existing project), vanilla JS (ES2017+, no build step), SCSS compiled via the `sass` CLI (dart-sass, already installed globally) to plain CSS, Leaflet.js (loaded from its public CDN, same as the CARTO tiles/Geonorge APIs which are already CDN-based in the reference), Kartverket's free `ws.geonorge.no` address APIs.

**Spec:** `kobly-full-site-spec.pdf` (repo root) — see especially §3 (design system), §4.4 (shared building blocks note on postnummer→wizard handoff), §5 (full wizard spec), §12 (receipt email), §15 (known quirks), §16 (rebuild architecture). Reference source/assets: `C:\Users\Bibi\Downloads\kobly\kobly\kobly-companion-files.zip` (already unzipped for this session at `C:\Users\Bibi\AppData\Local\Temp\claude\c--Users-Bibi-Desktop-orders-kobly\7a46541a-e5e9-48b5-adc2-214ae16bd29c\scratchpad\companion\` — re-unzip if that temp path is gone) — `app/wizard/page.tsx` and `components/wizard/MapPickerOverlay.tsx` are the authoritative behavioral references read in full for this plan.

## Global Constraints

- **Visual/word fidelity is the top priority.** Colors, fonts, radii, shadows, spacing, copy (Norwegian, verbatim from spec §5.12), and animation timings must match the reference 1:1 — this is a pixel/word-parity port, not a reinterpretation.
- **HTML must be simple and readable, not a utility-class soup.** Use plain, descriptive class names (`card`, `box`, `step`, `field`, `pill`, `panel`, etc., prefixed per-component, e.g. `wizard-card`, `wizard-step`, `address-field`, `pill-button`) instead of Tailwind-style atomic classes. Comment each major HTML section (`<!-- Step 1: address + map -->` etc.) so a reader can navigate the file without cross-referencing the spec.
- **SCSS must use nested parent/child rules** (`.wizard-card { .wizard-card__header { ... } }`), one file per concern, each section preceded by a `//` comment banner explaining what it styles. Compile with `sass <src>.scss <dest>.css --style=expanded` (no minification — keep it readable) after every edit; commit both the `.scss` source and compiled `.css`.
- **JS must be vanilla, no framework, and every function gets a one-line doc comment** above it explaining what it does and why (not just restating the name).
- **Server-side validation is the source of truth.** Every rule in spec §5.5–5.9 must be re-implemented in `WizardForm`; client-side JS validation only toggles the disabled state of the "Neste" button.
- **No client-side persistence** (no localStorage, no URL step param) — matches spec §5.11 exactly; a refresh mid-wizard resets to step 1, same as the reference.
- **Test runner:** `python manage.py test` (Django's built-in `unittest`-based runner — this project has no pytest installed; `apps/core/tests.py` already uses `django.test.TestCase`, so follow that convention). Run tests with whatever Python has Django installed on this machine (the checked-in `env/` venv is broken on this machine — `C:\Users\Bibi\AppData\Local\Programs\Python\Python312\python` has Django 5.1 available and was used to run `manage.py check` successfully earlier in this project).
- **Email in dev:** use Django's console `EmailBackend` so receipt emails print to the runserver console instead of attempting real SMTP delivery (no mail server is configured anywhere in this project yet).

---

## File structure (final state after this plan)

```
apps/leads/                          # new Django app
  __init__.py
  apps.py
  models.py            # MoveLead, LeadImage
  forms.py             # WizardForm
  cities.py            # CITIES dict (lat/lon/zoom per spec §13.1)
  emails.py            # send_receipt_email(lead)
  views.py             # wizard(request), wizard_thank_you(request)
  urls.py              # app_name = "leads"
  admin.py             # MoveLead/LeadImage admin registration
  migrations/0001_initial.py
  templates/leads/
    wizard.html
    thank_you.html
    emails/
      _shell.html       # shared table-based email wrapper (spec §12 emailShell())
      receipt.html       # extends _shell.html
  tests.py
static/
  fonts/
    Moderat-Regular.otf   # copied from companion bundle
    Moderat-Semibold.otf
  images/wizard/
    boxes-and-plants.jpg
    R1-09476-0023-kopi.jpg
    R1-07829-0034.jpg
    rull3_26.jpg
    R1-09476-0028.jpg
  scss/
    _kobly-tokens.scss   # design tokens (spec §3.1-3.3), used by wizard.scss
    wizard.scss           # wizard page styles, nested parent/child
  css/
    wizard.css            # compiled output of wizard.scss (includes tokens)
  js/
    wizard.js              # step controller, address autocomplete, maps, photo upload
demo/
  settings.py            # + apps.leads, EMAIL_BACKEND, MEDIA_ROOT
  urls.py                 # + include("apps.leads.urls")
```

**Naming contract used across every task below (do not deviate — later tasks depend on these exact names):**

- URL names: `leads:wizard` (`/wizard/`, GET+POST), `leads:wizard_thank_you` (`/wizard/takk/`, GET)
- `WizardForm` fields (exact names, used by both the HTML `name=` attributes and the view): `flytte_type, fra, fra_lat, fra_lon, til, til_lat, til_lon, boligtype, flyttedato, fleksibel, beskrivelse, navn, telefon, epost`. Photos are handled outside the form as `request.FILES.getlist("bilder")`.
- Model: `apps.leads.models.MoveLead`, `apps.leads.models.LeadImage`
- Email: `apps.leads.emails.send_receipt_email(lead: MoveLead) -> None`
- Top-level HTML/CSS classes (BEM-ish, `block__element`, `is-*` state modifiers): `.wizard`, `.wizard-card`, `.wizard-card__left`, `.wizard-card__right`, `.wizard-progress`, `.wizard-progress__segment.is-complete`, `.wizard-step.is-active`, `.step-header`, `.pill-group`, `.pill-button.is-selected`, `.address-field`, `.address-suggestions`, `.map-picker-btn.is-placed`, `.date-field`, `.flex-toggle.is-active`, `.photo-grid`, `.photo-thumb`, `.photo-upload-tile`, `.text-field`, `.wizard-nav`, `.wizard-nav__back`, `.wizard-nav__next`, `.map-panel`, `.map-panel__chip`, `.summary-panel`, `.summary-panel__row`, `.map-overlay`, `.thankyou`, `.thankyou-card`, `.thankyou-illustration`, `.btn-primary`, `.btn-text`.
- JS entry point: `static/js/wizard.js`, self-invoking, listens for `DOMContentLoaded`, calls `initWizard()`.

---

### Task 1: `leads` app scaffold + URL wiring

**Files:**
- Create: `apps/leads/__init__.py`, `apps/leads/apps.py`
- Create: `apps/leads/views.py`
- Create: `apps/leads/urls.py`
- Create: `apps/leads/templates/leads/wizard.html` (placeholder only — real markup comes in Task 8)
- Create: `apps/leads/tests.py`
- Modify: `demo/settings.py` — add `'apps.leads'` to `INSTALLED_APPS`
- Modify: `demo/urls.py` — add `path('wizard/', include('apps.leads.urls'))`

**Interfaces:**
- Produces: URL name `leads:wizard` resolving to `apps.leads.views.wizard`, mounted at `/wizard/`.

- [ ] **Step 1: Write the failing test**

```python
# apps/leads/tests.py
from django.test import TestCase
from django.urls import reverse


class WizardViewSmokeTest(TestCase):
    def test_get_wizard_page_returns_200(self):
        response = self.client.get(reverse("leads:wizard"))
        self.assertEqual(response.status_code, 200)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.leads`
Expected: FAIL (`NoReverseMatch` — `leads:wizard` doesn't exist yet, or app not installed)

- [ ] **Step 3: Write the app scaffold**

```python
# apps/leads/__init__.py
```

```python
# apps/leads/apps.py
from django.apps import AppConfig


class LeadsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.leads"
    label = "leads"
```

```python
# apps/leads/views.py
from django.shortcuts import render


def wizard(request):
    """Renders the 5-step lead-capture wizard (GET) — POST handling added in Task 5."""
    return render(request, "leads/wizard.html")
```

```python
# apps/leads/urls.py
from django.urls import path

from . import views

app_name = "leads"

urlpatterns = [
    path("", views.wizard, name="wizard"),
]
```

```html
<!-- apps/leads/templates/leads/wizard.html -->
<!-- Placeholder — replaced with the full 5-step markup in Task 8. -->
<!DOCTYPE html>
<html lang="nb">
<head><meta charset="UTF-8"><title>Kobly</title></head>
<body></body>
</html>
```

Modify `demo/settings.py` — inside the existing `INSTALLED_APPS` list, add the new app after the other local apps:

```python
    INSTALLED_APPS = [
        'django.contrib.sites',
        'allauth',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.sitemaps',
        'ckeditor',
        'apps.core',
        'apps.store',
        'apps.userprofile',
        'apps.leads',
    ]
```

Modify `demo/urls.py` — add the import and the include (keep every existing line, just add these):

```python
from django.urls import path, include
```

and inside `urlpatterns`, add:

```python
    path('wizard/', include('apps.leads.urls')),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.leads`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/leads demo/settings.py demo/urls.py
git commit -m "feat: scaffold leads app and mount /wizard/ route"
```

---

### Task 2: `MoveLead` and `LeadImage` models

**Files:**
- Create: `apps/leads/models.py`
- Create: `apps/leads/migrations/__init__.py`, `apps/leads/migrations/0001_initial.py` (via `makemigrations`)
- Create: `apps/leads/admin.py`
- Modify: `demo/settings.py` — add `MEDIA_ROOT` (currently only `MEDIA_URL` is set; `LeadImage` needs real local file storage)
- Modify: `apps/leads/tests.py` — add model tests

**Interfaces:**
- Produces: `MoveLead(flytte_type, fra, fra_lat, fra_lon, til, til_lat, til_lon, boligtype, flyttedato, fleksibel, beskrivelse, navn, telefon, epost, reference, created_at)`, `MoveLead.FLYTTE_TYPE_CHOICES`, `MoveLead.BOLIGTYPE_CHOICES`, `LeadImage(lead, image, uploaded_at)`.

- [ ] **Step 1: Write the failing test**

```python
# apps/leads/tests.py — add below the existing test class
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.leads.models import LeadImage, MoveLead


class MoveLeadModelTest(TestCase):
    def _make_lead(self, **overrides):
        data = dict(
            flytte_type="privat",
            fra="Kongens gate 1, 0153 Oslo",
            til="Storgata 14, 0184 Oslo",
            boligtype="leilighet",
            navn="Ola Nordmann",
            telefon="+47 900 00 000",
            epost="ola@eksempel.no",
        )
        data.update(overrides)
        return MoveLead.objects.create(**data)

    def test_reference_is_generated_on_save(self):
        lead = self._make_lead()
        self.assertTrue(lead.reference.startswith(f"KOB-{lead.created_at.year}-"))
        self.assertTrue(lead.reference.endswith(str(lead.pk)))

    def test_str_includes_reference_and_name(self):
        lead = self._make_lead()
        self.assertIn(lead.reference, str(lead))
        self.assertIn("Ola Nordmann", str(lead))

    def test_lead_image_attaches_to_lead(self):
        lead = self._make_lead()
        image = LeadImage.objects.create(
            lead=lead,
            image=SimpleUploadedFile("sofa.jpg", b"fake-image-bytes", content_type="image/jpeg"),
        )
        self.assertEqual(lead.images.count(), 1)
        self.assertEqual(lead.images.first(), image)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.leads`
Expected: FAIL (`ImportError` — `apps.leads.models` has no `MoveLead`/`LeadImage`)

- [ ] **Step 3: Write the models**

```python
# apps/leads/models.py
from django.db import models


class MoveLead(models.Model):
    """
    One submitted /wizard request. Field set and validation rules mirror
    the WizardData shape in kobly-full-site-spec.pdf §5.4 exactly — this
    model is the Django-side contract the wizard form/view fill in.
    """

    FLYTTE_TYPE_CHOICES = [
        ("privat", "Privat"),
        ("bedrift", "Bedrift"),
        ("internasjonal", "Internasjonal"),
    ]
    BOLIGTYPE_CHOICES = [
        ("leilighet", "Leilighet"),
        ("rekkehus", "Rekkehus"),
        ("enebolig", "Enebolig"),
        ("annet", "Annet"),
    ]

    # Auto-generated in save(), e.g. "KOB-2026-42" — used as the customer-facing
    # reference number in the receipt email (spec §12 LEAD.ref).
    reference = models.CharField(max_length=32, unique=True, editable=False, blank=True)

    # Step 2
    flytte_type = models.CharField(max_length=20, choices=FLYTTE_TYPE_CHOICES)
    boligtype = models.CharField(max_length=20, choices=BOLIGTYPE_CHOICES)

    # Step 1 — coordinates are optional (spec §5.5: "coordinates NOT required" to advance)
    fra = models.CharField(max_length=255)
    fra_lat = models.FloatField(null=True, blank=True)
    fra_lon = models.FloatField(null=True, blank=True)
    til = models.CharField(max_length=255)
    til_lat = models.FloatField(null=True, blank=True)
    til_lon = models.FloatField(null=True, blank=True)

    # Step 3 — date XOR flexible, enforced in WizardForm.clean(), not here
    flyttedato = models.DateField(null=True, blank=True)
    fleksibel = models.BooleanField(default=False)

    # Step 4 — always-optional
    beskrivelse = models.TextField(blank=True, default="")

    # Step 5
    navn = models.CharField(max_length=200)
    telefon = models.CharField(max_length=50)
    epost = models.EmailField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} — {self.navn}"

    def save(self, *args, **kwargs):
        # reference needs self.pk, so it's assigned on first save and then
        # persisted with a second save() call — cheap, and only runs once per lead.
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.reference:
            self.reference = f"KOB-{self.created_at.year}-{self.pk}"
            super().save(update_fields=["reference"])


class LeadImage(models.Model):
    """One uploaded photo attached to a MoveLead (spec §5.8 'bilder')."""

    lead = models.ForeignKey(MoveLead, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="leads/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.lead.reference}"
```

```python
# apps/leads/admin.py
from django.contrib import admin

from .models import LeadImage, MoveLead


class LeadImageInline(admin.TabularInline):
    model = LeadImage
    extra = 0


@admin.register(MoveLead)
class MoveLeadAdmin(admin.ModelAdmin):
    list_display = ("reference", "navn", "flytte_type", "boligtype", "fra", "til", "created_at")
    list_filter = ("flytte_type", "boligtype", "fleksibel")
    search_fields = ("reference", "navn", "epost", "telefon", "fra", "til")
    inlines = [LeadImageInline]
```

Modify `demo/settings.py` — `MEDIA_URL` is set but `MEDIA_ROOT` never was (it silently fell back to Django's empty-string default). Add it right after `MEDIA_URL`:

```python
    MEDIA_URL = 'images/'
    MEDIA_ROOT = BASE_DIR / 'media'
```

`ImageField` requires Pillow — check it's already available (it almost certainly is, since `apps/store` already uses image fields per the earlier `BusinessImage` migration):

Run: `python -c "import PIL; print(PIL.__version__)"` — if this fails, run `pip install Pillow` before continuing.

- [ ] **Step 4: Make and apply the migration**

Run: `python manage.py makemigrations leads`
Expected: creates `apps/leads/migrations/0001_initial.py` with `MoveLead` and `LeadImage`

Run: `python manage.py migrate leads`
Expected: applies cleanly

- [ ] **Step 5: Run test to verify it passes**

Run: `python manage.py test apps.leads`
Expected: PASS (3 new tests + the Task 1 smoke test)

- [ ] **Step 6: Commit**

```bash
git add apps/leads/models.py apps/leads/admin.py apps/leads/migrations apps/leads/tests.py demo/settings.py
git commit -m "feat: add MoveLead and LeadImage models"
```

---

### Task 3: `WizardForm` server-side validation

**Files:**
- Create: `apps/leads/forms.py`
- Modify: `apps/leads/tests.py` — add form tests

**Interfaces:**
- Consumes: `MoveLead.FLYTTE_TYPE_CHOICES`, `MoveLead.BOLIGTYPE_CHOICES` (Task 2)
- Produces: `WizardForm(forms.Form)` with `.is_valid()` / `.cleaned_data` covering all fields from the naming contract above. `.cleaned_data` keys map 1:1 to `MoveLead` field names so `MoveLead.objects.create(**form.cleaned_data)` works directly in Task 5.

- [ ] **Step 1: Write the failing test**

```python
# apps/leads/tests.py — add below MoveLeadModelTest
from apps.leads.forms import WizardForm


def _valid_payload(**overrides):
    data = dict(
        flytte_type="privat",
        fra="Kongens gate 1, 0153 Oslo",
        fra_lat="59.913",
        fra_lon="10.752",
        til="Storgata 14, 0184 Oslo",
        til_lat="",
        til_lon="",
        boligtype="leilighet",
        flyttedato="2026-09-12",
        fleksibel="",
        beskrivelse="3-seters sofa",
        navn="Ola Nordmann",
        telefon="+47 900 00 000",
        epost="ola@eksempel.no",
    )
    data.update(overrides)
    return data


class WizardFormTest(TestCase):
    def test_valid_payload_passes(self):
        form = WizardForm(_valid_payload())
        self.assertTrue(form.is_valid(), form.errors)

    def test_fra_shorter_than_3_chars_is_invalid(self):
        form = WizardForm(_valid_payload(fra="Os"))
        self.assertFalse(form.is_valid())
        self.assertIn("fra", form.errors)

    def test_til_shorter_than_3_chars_is_invalid(self):
        form = WizardForm(_valid_payload(til="St"))
        self.assertFalse(form.is_valid())
        self.assertIn("til", form.errors)

    def test_coordinates_are_optional(self):
        form = WizardForm(_valid_payload(fra_lat="", fra_lon="", til_lat="", til_lon=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_flytte_type_is_invalid(self):
        form = WizardForm(_valid_payload(flytte_type=""))
        self.assertFalse(form.is_valid())
        self.assertIn("flytte_type", form.errors)

    def test_missing_boligtype_is_invalid(self):
        form = WizardForm(_valid_payload(boligtype=""))
        self.assertFalse(form.is_valid())
        self.assertIn("boligtype", form.errors)

    def test_missing_date_and_not_flexible_is_invalid(self):
        form = WizardForm(_valid_payload(flyttedato="", fleksibel=""))
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_flexible_without_date_is_valid(self):
        form = WizardForm(_valid_payload(flyttedato="", fleksibel="on"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_beskrivelse_is_always_optional(self):
        form = WizardForm(_valid_payload(beskrivelse=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_navn_single_char_is_invalid(self):
        form = WizardForm(_valid_payload(navn="O"))
        self.assertFalse(form.is_valid())
        self.assertIn("navn", form.errors)

    def test_telefon_too_short_is_invalid(self):
        form = WizardForm(_valid_payload(telefon="123"))
        self.assertFalse(form.is_valid())
        self.assertIn("telefon", form.errors)

    def test_telefon_allows_spaces_and_plus(self):
        form = WizardForm(_valid_payload(telefon="+47 900 00 000"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_epost_without_at_sign_is_invalid(self):
        form = WizardForm(_valid_payload(epost="ikke-en-epost"))
        self.assertFalse(form.is_valid())
        self.assertIn("epost", form.errors)

    def test_epost_permissive_pattern_accepts_short_domain(self):
        # Spec §5.9: /\S+@\S+\.\S+/ — permissive, not RFC-strict.
        form = WizardForm(_valid_payload(epost="a@b.co"))
        self.assertTrue(form.is_valid(), form.errors)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.leads`
Expected: FAIL (`ImportError` — `apps.leads.forms` doesn't exist)

- [ ] **Step 3: Write the form**

```python
# apps/leads/forms.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.leads`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/leads/forms.py apps/leads/tests.py
git commit -m "feat: add WizardForm with server-side validation matching spec §5.5-5.9"
```

---

### Task 4: `wizard` view — GET with query-string prefill (`?fra=`, `?by=`)

**Files:**
- Create: `apps/leads/cities.py`
- Modify: `apps/leads/views.py`
- Modify: `apps/leads/tests.py`

**Interfaces:**
- Produces: `apps.leads.cities.CITIES` (dict keyed by city slug → `{"name", "lat", "lon", "zoom"}`), used by the view to compute `initial_center` context.
- Consumes: `WizardForm` (Task 3) for the initial unbound form with `fra` prefilled.

- [ ] **Step 1: Write the failing test**

```python
# apps/leads/tests.py — add
import json


class WizardGetViewTest(TestCase):
    def test_fra_query_param_prefills_form(self):
        response = self.client.get(reverse("leads:wizard"), {"fra": "1170"})
        self.assertContains(response, 'value="1170"')

    def test_by_query_param_sets_initial_center(self):
        response = self.client.get(reverse("leads:wizard"), {"by": "bergen"})
        center = json.loads(response.context["initial_center_json"])
        self.assertEqual(center["lat"], 60.3913)
        self.assertEqual(center["zoom"], 11)

    def test_unknown_by_query_param_is_ignored(self):
        response = self.client.get(reverse("leads:wizard"), {"by": "narnia"})
        self.assertEqual(response.context["initial_center_json"], "null")

    def test_no_by_query_param_gives_null_center(self):
        response = self.client.get(reverse("leads:wizard"))
        self.assertEqual(response.context["initial_center_json"], "null")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.leads`
Expected: FAIL (view doesn't pass `initial_center_json`/prefill yet)

- [ ] **Step 3: Implement**

```python
# apps/leads/cities.py
"""
The 5 cities the wizard's map can be pre-centered on via ?by=<slug>.
Verbatim from kobly-full-site-spec.pdf §13.1 / the reference lib/cities.ts.
Reused later by the city marketing pages (a later phase).
"""

CITIES = {
    "oslo": {"name": "Oslo", "lat": 59.9139, "lon": 10.7522, "zoom": 11},
    "bergen": {"name": "Bergen", "lat": 60.3913, "lon": 5.3221, "zoom": 11},
    "trondheim": {"name": "Trondheim", "lat": 63.4305, "lon": 10.3951, "zoom": 11},
    "stavanger": {"name": "Stavanger", "lat": 58.9700, "lon": 5.7331, "zoom": 11},
    "tromso": {"name": "Tromsø", "lat": 69.6492, "lon": 18.9553, "zoom": 11},
}
```

```python
# apps/leads/views.py
import json

from django.shortcuts import render

from .cities import CITIES
from .forms import WizardForm


def wizard(request):
    """
    Renders the 5-step lead-capture wizard.

    GET: shows an empty form, optionally pre-filled from the query string —
    ?fra=<text> drops straight into the free-text "Fra adresse" field with
    no lookup (spec §4.4 note: this low-fidelity behavior is preserved on
    purpose, matching the reference exactly) and ?by=<city slug> centers the
    map before the user has typed anything (spec §5.1/§7).

    POST: validates and saves the lead — added in Task 5.
    """
    initial = {"fra": request.GET.get("fra", "")}
    form = WizardForm(initial=initial)

    by = request.GET.get("by")
    initial_center = CITIES.get(by) if by else None

    context = {
        "form": form,
        "initial_center_json": json.dumps(initial_center),
    }
    return render(request, "leads/wizard.html", context)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.leads`
Expected: PASS

Note: this test relies on the placeholder template not erroring when `{{ form }}`/`{{ initial_center_json }}` aren't referenced yet — Django doesn't error on unused context variables, so the Task 1 placeholder template still renders fine. The `value="1170"` assertion requires the real template (Task 8) to actually render `{{ form.fra }}`; until Task 8 lands, temporarily add `{{ form.fra }}` to the placeholder template so this test is meaningful now rather than silently trivial:

```html
<!-- apps/leads/templates/leads/wizard.html -->
<!DOCTYPE html>
<html lang="nb">
<head><meta charset="UTF-8"><title>Kobly</title></head>
<body>{{ form.fra }}</body>
</html>
```

- [ ] **Step 5: Commit**

```bash
git add apps/leads/cities.py apps/leads/views.py apps/leads/templates/leads/wizard.html apps/leads/tests.py
git commit -m "feat: wizard GET view with ?fra=/?by= prefill"
```

---

### Task 5: `wizard` view — POST, save `MoveLead` + `LeadImage`, redirect to thank-you

**Files:**
- Modify: `apps/leads/views.py`
- Modify: `apps/leads/urls.py`
- Create: `apps/leads/templates/leads/thank_you.html` (placeholder — real markup in Task 8)
- Modify: `apps/leads/tests.py`

**Interfaces:**
- Consumes: `WizardForm` (Task 3), `MoveLead`/`LeadImage` (Task 2)
- Produces: URL name `leads:wizard_thank_you`.

- [ ] **Step 1: Write the failing test**

```python
# apps/leads/tests.py — add
class WizardPostViewTest(TestCase):
    def test_valid_post_creates_lead_and_redirects(self):
        response = self.client.post(reverse("leads:wizard"), _valid_payload())
        self.assertRedirects(response, reverse("leads:wizard_thank_you"))
        self.assertEqual(MoveLead.objects.count(), 1)
        lead = MoveLead.objects.get()
        self.assertEqual(lead.navn, "Ola Nordmann")
        self.assertEqual(lead.flytte_type, "privat")

    def test_valid_post_with_photos_creates_lead_images(self):
        payload = _valid_payload()
        photo = SimpleUploadedFile("sofa.jpg", b"fake-bytes", content_type="image/jpeg")
        response = self.client.post(reverse("leads:wizard"), {**payload, "bilder": [photo]})
        self.assertRedirects(response, reverse("leads:wizard_thank_you"))
        lead = MoveLead.objects.get()
        self.assertEqual(lead.images.count(), 1)

    def test_invalid_post_rerenders_form_with_errors(self):
        response = self.client.post(reverse("leads:wizard"), _valid_payload(navn="O"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MoveLead.objects.count(), 0)
        self.assertTrue(response.context["form"].errors)

    def test_thank_you_page_returns_200(self):
        response = self.client.get(reverse("leads:wizard_thank_you"))
        self.assertEqual(response.status_code, 200)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.leads`
Expected: FAIL (`NoReverseMatch` for `leads:wizard_thank_you`, POST not handled)

- [ ] **Step 3: Implement**

```python
# apps/leads/views.py — replace the wizard() function with this, keep the imports/cities/form import
import json

from django.shortcuts import redirect, render

from .cities import CITIES
from .emails import send_receipt_email
from .forms import WizardForm
from .models import LeadImage, MoveLead


def wizard(request):
    """
    Renders the 5-step lead-capture wizard (GET) and processes the final
    submission (POST). See module docstring context in Task 4 for the GET
    pre-fill behavior.
    """
    if request.method == "POST":
        form = WizardForm(request.POST)
        if form.is_valid():
            lead = MoveLead.objects.create(**form.cleaned_data)
            for uploaded_file in request.FILES.getlist("bilder"):
                LeadImage.objects.create(lead=lead, image=uploaded_file)
            send_receipt_email(lead)
            return redirect("leads:wizard_thank_you")
        # Invalid: fall through and re-render the wizard with errors attached.
        # This only happens if a client bypasses the JS validation — the
        # normal path always submits data the JS has already confirmed valid.
        initial_center = None
    else:
        form = WizardForm(initial={"fra": request.GET.get("fra", "")})
        by = request.GET.get("by")
        initial_center = CITIES.get(by) if by else None

    context = {
        "form": form,
        "initial_center_json": json.dumps(initial_center),
    }
    return render(request, "leads/wizard.html", context)


def wizard_thank_you(request):
    """Static thank-you screen shown after a successful submit (spec §5.10)."""
    return render(request, "leads/thank_you.html")
```

```python
# apps/leads/urls.py
from django.urls import path

from . import views

app_name = "leads"

urlpatterns = [
    path("", views.wizard, name="wizard"),
    path("takk/", views.wizard_thank_you, name="wizard_thank_you"),
]
```

```html
<!-- apps/leads/templates/leads/thank_you.html -->
<!-- Placeholder — replaced with the real thank-you markup in Task 8. -->
<!DOCTYPE html>
<html lang="nb">
<head><meta charset="UTF-8"><title>Kobly</title></head>
<body>Forespørselen er sendt!</body>
</html>
```

`send_receipt_email` doesn't exist yet — stub it so this task's tests pass in isolation; Task 7 replaces the stub with the real implementation:

```python
# apps/leads/emails.py
def send_receipt_email(lead):
    """Stub — replaced with the real implementation in Task 7."""
    pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.leads`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/leads/views.py apps/leads/urls.py apps/leads/emails.py apps/leads/templates/leads/thank_you.html apps/leads/tests.py
git commit -m "feat: handle wizard POST — save MoveLead/LeadImage, redirect to thank-you"
```

---

### Task 6: Receipt email (real implementation)

**Files:**
- Modify: `apps/leads/emails.py`
- Create: `apps/leads/templates/leads/emails/_shell.html`
- Create: `apps/leads/templates/leads/emails/receipt.html`
- Modify: `demo/settings.py` — `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`
- Modify: `apps/leads/tests.py`

**Interfaces:**
- Consumes: `MoveLead` (Task 2)
- Produces: `send_receipt_email(lead)` sends one email via Django's `mail.outbox` in tests / console backend in dev.

This ports `lib/emails/receipt.ts` + `lib/emails/layout.ts`'s `emailShell()`/`card()`/`detailRow()`/`stepsList()` building blocks (spec §12) into Django templates — table-based, fully inlined styles, no external CSS, matching the reference's email-client-safe structure exactly. One adaptation, documented here rather than silently copied: the reference's dummy email data includes a `tjenester` ("services") row that has no corresponding field anywhere in the actual wizard (§5.4's `WizardData` has no services multi-select) — it only exists in the reference's hand-written preview dummy data. This port uses the wizard's real `beskrivelse` field for that row instead ("Om tingene dine" / the lead's own description text), since that's the closest real field to what that row was showing.

- [ ] **Step 1: Write the failing test**

```python
# apps/leads/tests.py — add
from django.core import mail

from apps.leads.emails import send_receipt_email


class ReceiptEmailTest(TestCase):
    def test_sends_one_email_to_the_lead(self):
        lead = MoveLead.objects.create(
            flytte_type="privat",
            fra="Kongens gate 1, 0153 Oslo",
            til="Storgata 14, 0184 Oslo",
            boligtype="leilighet",
            flyttedato="2026-09-12",
            navn="Ola Nordmann",
            telefon="+47 900 00 000",
            epost="ola@eksempel.no",
        )
        send_receipt_email(lead)
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, ["ola@eksempel.no"])
        self.assertEqual(sent.subject, "Vi har mottatt flytteforespørselen din")
        self.assertIn(lead.reference, sent.alternatives[0][0])
        self.assertIn("Ola Nordmann", sent.alternatives[0][0])

    def test_flexible_date_shows_fleksibel_dato_label(self):
        lead = MoveLead.objects.create(
            flytte_type="privat",
            fra="Kongens gate 1, 0153 Oslo",
            til="Storgata 14, 0184 Oslo",
            boligtype="leilighet",
            fleksibel=True,
            navn="Kari Nordmann",
            telefon="+47 900 00 000",
            epost="kari@eksempel.no",
        )
        send_receipt_email(lead)
        self.assertIn("Fleksibel dato", mail.outbox[0].alternatives[0][0])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.leads`
Expected: FAIL (stub sends nothing)

- [ ] **Step 3: Implement**

```html
<!-- apps/leads/templates/leads/emails/_shell.html -->
{% comment %}
Shared table-based email wrapper — every Kobly transactional email extends
this. Ported from lib/emails/layout.ts's emailShell(): centered logo, white
content card, footer with company address/contact/unsubscribe links.
Email-client-safe on purpose: tables for layout, every style inlined,
system fonts only, no external CSS/JS. Don't "clean this up" with classes —
Outlook and older Gmail ignore <style> blocks for layout-critical rules.
{% endcomment %}
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="nb">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Kobly</title>
<!--[if mso]>
<style type="text/css">body, table, td, a { font-family: Arial, Helvetica, sans-serif !important; }</style>
<![endif]-->
</head>
<body style="margin:0; padding:0; background-color:#f4f1ea;">
  <div style="display:none; max-height:0; overflow:hidden; opacity:0; mso-hide:all;">{{ preheader }}</div>
  <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color:#f4f1ea;">
    <tr>
      <td align="center" style="padding:24px 12px 40px;">
        <table role="presentation" width="600" border="0" cellpadding="0" cellspacing="0" style="width:100%; max-width:600px;">

          <!-- Logo -->
          <tr>
            <td align="center" style="padding:16px 32px 24px; text-align:center;">
              <a href="https://kobly.no/" style="text-decoration:none; font-family:Georgia, serif; font-size:22px; font-weight:bold; color:#221814;">Kobly</a>
            </td>
          </tr>

          <!-- Content card -->
          <tr>
            <td style="background-color:#ffffff; border:1px solid #e6e1d6; border-radius:14px;">
              <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
                {% block content %}{% endblock %}
                <tr><td style="height:36px; line-height:36px; font-size:0;">&nbsp;</td></tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:28px 32px 0;">
              <p style="margin:0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:13px; line-height:1.6; color:#5c5c5c;">
                {{ footer_note }}
              </p>
              <p style="margin:14px 0 0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:13px; line-height:1.6; color:#5c5c5c;">
                Kobly AS &middot; Torggata 15, 0181 Oslo<br />
                <a href="mailto:hei@kobly.no" style="color:#5c5c5c; text-decoration:underline;">hei@kobly.no</a> &middot; 21 09 88 00
              </p>
              <p style="margin:18px 0 0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:12px; line-height:1.6; color:#8a8a8a;">
                &copy; 2026 Kobly AS
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

```html
<!-- apps/leads/templates/leads/emails/receipt.html -->
{% extends "leads/emails/_shell.html" %}
{% comment %}
Ported from lib/emails/receipt.ts. `lead` is a MoveLead instance passed in
from send_receipt_email(). See Task 6's note above on the beskrivelse/
tjenester adaptation.
{% endcomment %}

{% block content %}
<tr>
  <td style="padding:36px 32px 0;">
    <h1 style="margin:0; font-family:Georgia, 'Times New Roman', Times, serif; font-size:28px; line-height:1.2; font-weight:normal; color:#1a1a1a;">Takk, vi har mottatt forespørselen din</h1>
  </td>
</tr>
<tr>
  <td style="padding:16px 32px 0;">
    <p style="margin:0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:16px; line-height:1.65; color:#1a1a1a;">Hei {{ lead.navn }}! Forespørselen din er registrert, og vi er allerede i gang med å finne byråer som passer. Her er det du sendte inn:</p>
  </td>
</tr>

<!-- Summary card: reference + submitted fields -->
<tr>
  <td style="padding:24px 32px 0;">
    <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color:#faf9f6; border:1px solid #e6e1d6; border-radius:14px;">
      <tr>
        <td style="padding:22px 24px;">
          <p style="margin:0 0 4px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:13px; font-weight:600; letter-spacing:0.02em; color:#5c5c5c;">Forespørsel {{ lead.reference }}</p>
          <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
            <tr>
              <td style="padding:14px 0; border-bottom:1px solid #e6e1d6;">
                <p style="margin:0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:13px; line-height:1.4; color:#5c5c5c;">Flytter fra</p>
                <p style="margin:4px 0 0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:16px; line-height:1.5; font-weight:600; color:#1a1a1a;">{{ lead.fra }}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:14px 0; border-bottom:1px solid #e6e1d6;">
                <p style="margin:0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:13px; line-height:1.4; color:#5c5c5c;">Flytter til</p>
                <p style="margin:4px 0 0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:16px; line-height:1.5; font-weight:600; color:#1a1a1a;">{{ lead.til }}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:14px 0; border-bottom:1px solid #e6e1d6;">
                <p style="margin:0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:13px; line-height:1.4; color:#5c5c5c;">Ønsket dato</p>
                <p style="margin:4px 0 0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:16px; line-height:1.5; font-weight:600; color:#1a1a1a;">{% if lead.fleksibel %}Fleksibel dato{% else %}{{ lead.flyttedato|date:"j. F Y" }}{% endif %}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:14px 0; {% if lead.beskrivelse %}border-bottom:1px solid #e6e1d6;{% endif %}">
                <p style="margin:0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:13px; line-height:1.4; color:#5c5c5c;">Boligtype</p>
                <p style="margin:4px 0 0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:16px; line-height:1.5; font-weight:600; color:#1a1a1a;">{{ lead.get_boligtype_display }}</p>
              </td>
            </tr>
            {% if lead.beskrivelse %}
            <tr>
              <td style="padding:14px 0;">
                <p style="margin:0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:13px; line-height:1.4; color:#5c5c5c;">Om tingene dine</p>
                <p style="margin:4px 0 0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:16px; line-height:1.5; font-weight:600; color:#1a1a1a;">{{ lead.beskrivelse }}</p>
              </td>
            </tr>
            {% endif %}
          </table>
        </td>
      </tr>
    </table>
  </td>
</tr>

<!-- "Slik går vi frem" steps list -->
<tr>
  <td style="padding:32px 32px 0;">
    <p style="margin:0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:16px; font-weight:600; line-height:1.5; color:#1a1a1a;">Slik går vi frem</p>
  </td>
</tr>
<tr>
  <td style="padding:18px 32px 0;">
    <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
      <tr>
        <td width="34" valign="top" style="padding:0 0 16px;">
          <table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td width="26" height="26" align="center" valign="middle" bgcolor="#d6e8a8" style="width:26px; height:26px; border-radius:13px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:13px; font-weight:600; color:#1a1a1a;">1</td></tr></table>
        </td>
        <td valign="top" style="padding:0 0 16px;">
          <p style="margin:2px 0 0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:15px; line-height:1.6; color:#1a1a1a;">Vi matcher deg med 3 kvalitetssjekkede byråer som passer flyttingen din.</p>
        </td>
      </tr>
      <tr>
        <td width="34" valign="top" style="padding:0 0 16px;">
          <table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td width="26" height="26" align="center" valign="middle" bgcolor="#d6e8a8" style="width:26px; height:26px; border-radius:13px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:13px; font-weight:600; color:#1a1a1a;">2</td></tr></table>
        </td>
        <td valign="top" style="padding:0 0 16px;">
          <p style="margin:2px 0 0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:15px; line-height:1.6; color:#1a1a1a;">Byråene kontakter deg med tilbud innen 24 timer.</p>
        </td>
      </tr>
      <tr>
        <td width="34" valign="top">
          <table role="presentation" border="0" cellpadding="0" cellspacing="0"><tr><td width="26" height="26" align="center" valign="middle" bgcolor="#d6e8a8" style="width:26px; height:26px; border-radius:13px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:13px; font-weight:600; color:#1a1a1a;">3</td></tr></table>
        </td>
        <td valign="top">
          <p style="margin:2px 0 0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:15px; line-height:1.6; color:#1a1a1a;">Du sammenligner og velger. Helt uforpliktende.</p>
        </td>
      </tr>
    </table>
  </td>
</tr>

<!-- Closing note -->
<tr>
  <td style="padding:28px 32px 0;">
    <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
      <tr>
        <td style="border-top:1px solid #e6e1d6; padding-top:22px;">
          <p style="margin:0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size:14px; line-height:1.65; color:#5c5c5c;">Du trenger ikke gjøre noe nå. Vil du endre noe i forespørselen, er det bare å svare på denne e-posten, så ordner vi det.</p>
        </td>
      </tr>
    </table>
  </td>
</tr>
{% endblock %}
```

```python
# apps/leads/emails.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

RECEIPT_SUBJECT = "Vi har mottatt flytteforespørselen din"


def send_receipt_email(lead):
    """
    Sends the "we received your request" email to the customer, immediately
    after a successful wizard submit (spec §12, template id "receipt").
    """
    html = render_to_string(
        "leads/emails/receipt.html",
        {
            "lead": lead,
            "preheader": "Vi matcher deg med tre kvalitetssjekkede byråer. Du hører fra dem innen 24 timer.",
            "footer_note": "Du får denne e-posten fordi du sendte inn en flytteforespørsel på kobly.no.",
        },
    )
    message = EmailMultiAlternatives(
        subject=RECEIPT_SUBJECT,
        body=f"Hei {lead.navn}, vi har mottatt forespørselen din ({lead.reference}).",
        to=[lead.epost],
    )
    message.attach_alternative(html, "text/html")
    message.send()
```

Modify `demo/settings.py` — add near the bottom, alongside the other constants:

```python
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'Kobly <hei@kobly.no>'
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.leads`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/leads/emails.py apps/leads/templates/leads/emails demo/settings.py apps/leads/tests.py
git commit -m "feat: send receipt email on successful wizard submit"
```

---

### Task 7: Design tokens SCSS + fonts + wizard images

**Files:**
- Create: `static/scss/_kobly-tokens.scss`
- Create: `static/fonts/Moderat-Regular.otf`, `static/fonts/Moderat-Semibold.otf` (copy from companion bundle)
- Create: `static/images/wizard/boxes-and-plants.jpg`, `R1-09476-0023-kopi.jpg`, `R1-07829-0034.jpg`, `rull3_26.jpg`, `R1-09476-0028.jpg` (copy from companion bundle)

**Interfaces:**
- Produces: SCSS variables `$color-bg, $color-surface, $color-surface-soft, $color-ink, $color-ink-muted, $color-line, $color-brand, $color-brand-ink, $color-accent-lime, $color-accent-amber, $color-olive, $font-sans, $font-serif, $radius-card, $radius-pill, $shadow-elevated` — consumed by `wizard.scss` in Task 9. Also the `@font-face` rules and a `%` placeholder for the "cv11" feature-setting.

- [ ] **Step 1: Copy the binary assets**

```bash
mkdir -p static/fonts static/images/wizard
cp "C:/Users/Bibi/AppData/Local/Temp/claude/c--Users-Bibi-Desktop-orders-kobly/7a46541a-e5e9-48b5-adc2-214ae16bd29c/scratchpad/companion/app/fonts/Moderat-Regular.otf" static/fonts/
cp "C:/Users/Bibi/AppData/Local/Temp/claude/c--Users-Bibi-Desktop-orders-kobly/7a46541a-e5e9-48b5-adc2-214ae16bd29c/scratchpad/companion/app/fonts/Moderat-Semibold.otf" static/fonts/
cp "C:/Users/Bibi/AppData/Local/Temp/claude/c--Users-Bibi-Desktop-orders-kobly/7a46541a-e5e9-48b5-adc2-214ae16bd29c/scratchpad/companion/public/images/boxes-and-plants.jpg" static/images/wizard/
cp "C:/Users/Bibi/AppData/Local/Temp/claude/c--Users-Bibi-Desktop-orders-kobly/7a46541a-e5e9-48b5-adc2-214ae16bd29c/scratchpad/companion/public/images/R1-09476-0023-kopi.jpg" static/images/wizard/
cp "C:/Users/Bibi/AppData/Local/Temp/claude/c--Users-Bibi-Desktop-orders-kobly/7a46541a-e5e9-48b5-adc2-214ae16bd29c/scratchpad/companion/public/images/R1-07829-0034.jpg" static/images/wizard/
cp "C:/Users/Bibi/AppData/Local/Temp/claude/c--Users-Bibi-Desktop-orders-kobly/7a46541a-e5e9-48b5-adc2-214ae16bd29c/scratchpad/companion/public/images/rull3_26.jpg" static/images/wizard/
cp "C:/Users/Bibi/AppData/Local/Temp/claude/c--Users-Bibi-Desktop-orders-kobly/7a46541a-e5e9-48b5-adc2-214ae16bd29c/scratchpad/companion/public/images/R1-09476-0028.jpg" static/images/wizard/
```

If that temp path no longer exists (session scratchpads are ephemeral), re-unzip first: `unzip -o "C:/Users/Bibi/Downloads/kobly/kobly/kobly-companion-files.zip" -d /tmp/kobly-companion` and copy from there instead.

- [ ] **Step 2: Write the design tokens**

```scss
// static/scss/_kobly-tokens.scss
//
// Kobly design system tokens — spec §3 (kobly-full-site-spec.pdf).
// One source of truth for color/type/shape values used by wizard.scss
// (and every later marketing-page SCSS file, in a future phase).
// Partial file (leading underscore) — imported with @use, never compiled
// standalone.

// --- Colors (spec §3.1) ---
$color-bg: #f4f1ea;
$color-surface: #ffffff;
$color-surface-soft: #faf9f6;
$color-ink: #1a1a1a;
$color-ink-muted: #5c5c5c;
$color-line: #e6e1d6;
$color-brand: #221814; // primary brand fill — CTAs, selected states, footer
$color-brand-ink: #faf9f6; // text/icon color placed on top of $color-brand
$color-accent-lime: #d6e8a8;
$color-accent-amber: #e8a87c;
$color-olive: #3d5507; // hardcoded outlier used only for checkmarks + the "to" map pin

// --- Type (spec §3.2) ---
$font-sans: "Moderat", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
$font-serif: "Crimson Pro", Georgia, "Times New Roman", serif;

// --- Shape / elevation (spec §3.3) ---
$radius-card: 14px;
$radius-pill: 9999px;
$shadow-card-elevated: 0 20px 60px rgba(0, 0, 0, 0.28), 0 4px 16px rgba(0, 0, 0, 0.1);

@font-face {
  font-family: "Moderat";
  src: url("/static/fonts/Moderat-Regular.otf") format("opentype");
  font-weight: 400;
  font-display: swap;
}

@font-face {
  font-family: "Moderat";
  src: url("/static/fonts/Moderat-Semibold.otf") format("opentype");
  font-weight: 600;
  font-display: swap;
}

// spec §3.2: cv11 on globally, ss01 deliberately left off (swaps ?/% glyphs
// for alternates missing from the Semibold weight — looks thin next to bold text).
%kobly-font-features {
  font-feature-settings: "cv11";
}
```

- [ ] **Step 3: Verify (no automated test — visual/asset-presence check)**

Run: `ls static/fonts static/images/wizard` and confirm all 7 files are present. There's no meaningful unit test for "did the binary files get copied" — this is a file-copy task, verified by listing, not `manage.py test`.

- [ ] **Step 4: Commit**

```bash
git add static/fonts static/images/wizard static/scss/_kobly-tokens.scss
git commit -m "feat: add Kobly design tokens, fonts, and wizard background images"
```

---

### Task 8: `wizard.html` — full page markup for all 5 steps

**Files:**
- Modify: `apps/leads/templates/leads/wizard.html` (replace placeholder)
- Modify: `apps/leads/tests.py`

**Interfaces:**
- Consumes: `form` and `initial_center_json` context vars (Task 4/5), the class-name contract from "File structure" above.
- Produces: the exact `data-step="N"` / `.wizard-step` / `.wizard-card__right` DOM structure that `wizard.scss` (Task 9) and `wizard.js` (Task 10-13) target — every class and `data-*` attribute name here is load-bearing for later tasks, don't rename without updating them too.

This is the single biggest template in the app — build it in one pass since it's one cohesive deliverable (one page, reviewed as a whole), but every section below is HTML-commented so it reads like 5 small documents stitched together.

- [ ] **Step 1: Write a rendering test first**

```python
# apps/leads/tests.py — add
class WizardTemplateRenderTest(TestCase):
    def test_renders_all_five_step_headings(self):
        response = self.client.get(reverse("leads:wizard"))
        content = response.content.decode()
        for heading in [
            "Hvor skal du flytte?",
            "Hva slags flytting er det?",
            "Når skal du flytte?",
            "Hva skal du flytte?",
            "La oss ta kontakt",
        ]:
            self.assertIn(heading, content)

    def test_renders_five_progress_segments(self):
        response = self.client.get(reverse("leads:wizard"))
        self.assertContains(response, 'class="wizard-progress__segment"', count=5)

    def test_renders_csrf_token(self):
        response = self.client.get(reverse("leads:wizard"))
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_thank_you_renders_confirmation_copy(self):
        response = self.client.get(reverse("leads:wizard_thank_you"))
        self.assertContains(response, "Forespørselen er sendt!")
        self.assertContains(response, "Tilbake til forsiden")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.leads`
Expected: FAIL (placeholder template has none of this)

- [ ] **Step 3: Write the template**

```html
<!-- apps/leads/templates/leads/wizard.html -->
{% load static %}
<!DOCTYPE html>
<html lang="nb">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kobly — Få 3 tilbud gratis</title>

  <!-- Crimson Pro is a free Google Font (spec §3.2) — Moderat is self-hosted, see wizard.css -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;500;600&display=swap" rel="stylesheet">

  <!-- Leaflet (map library) — loaded from its public CDN, same as the CARTO
       tiles and Geonorge APIs used below: all free/keyless per spec §5.13 -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">

  <link rel="stylesheet" href="{% static 'css/wizard.css' %}">
</head>
<body>

<!-- ============================================================ -->
<!-- WIZARD ROOT — fullscreen takeover, independent of page scroll -->
<!-- ============================================================ -->
<div class="wizard" data-total-steps="5">

  <!-- Desktop background: fixed calm photo under a light wash (spec §5.3) -->
  <div class="wizard__background wizard__background--desktop" aria-hidden="true">
    <img src="{% static 'images/wizard/boxes-and-plants.jpg' %}" alt="">
    <div class="wizard__background-wash"></div>
  </div>

  <!-- Mobile background: step-specific photo + dark scrim, crossfades on step change.
       Two stacked <img> elements (not one per step) — wizard.js swaps "current"'s src
       and briefly keeps the old photo visible in "prev" underneath it while the new one
       fades in, matching spec §5.3's crossfade technique. -->
  <div class="wizard__background wizard__background--mobile" aria-hidden="true">
    <img class="wizard__background-photo wizard__background-photo--prev" data-step-bg-prev alt="" hidden>
    <img class="wizard__background-photo wizard__background-photo--current" data-step-bg-current src="{% static 'images/wizard/boxes-and-plants.jpg' %}" alt="">
    <div class="wizard__background-scrim"></div>
  </div>

  <!-- Logo — floats over the photo on desktop, sits inline above the card on mobile -->
  <a href="/" class="wizard__logo wizard__logo--desktop" aria-label="Kobly hjem">
    {% include "leads/_logo.html" with tone="ink" %}
  </a>
  <div class="wizard__logo-row">
    <a href="/" class="wizard__logo wizard__logo--mobile" aria-label="Kobly hjem">
      {% include "leads/_logo.html" with tone="brand-ink" %}
    </a>
  </div>

  <!-- ============================================================ -->
  <!-- CARD — one form, all 5 steps, only one visible at a time (JS) -->
  <!-- ============================================================ -->
  <form class="wizard-card" method="post" enctype="multipart/form-data" novalidate>
    {% csrf_token %}
    <div class="wizard-card__body">

      <!-- LEFT COLUMN: progress bar, step content, bottom nav -->
      <div class="wizard-card__left">

        <!-- Progress bar: 5 segments, filled = completed steps only -->
        <div class="wizard-progress" role="presentation">
          <div class="wizard-progress__segment"></div>
          <div class="wizard-progress__segment"></div>
          <div class="wizard-progress__segment"></div>
          <div class="wizard-progress__segment"></div>
          <div class="wizard-progress__segment"></div>
        </div>
        <span class="wizard-steplabel">Steg <span data-current-step-label>1</span> av 5</span>

        <!-- ===================== STEP 1: address + map ===================== -->
        <section class="wizard-step is-active" data-step="1">
          <div class="step-header">
            <h1 class="step-header__title">Hvor skal du flytte?</h1>
            <p class="step-header__subtitle">Skriv inn fra-adresse og til-adresse</p>
          </div>

          <div class="wizard-step__body">
            <div class="address-field" data-address-field="fra">
              <label class="field-label" for="id_fra">Fra adresse</label>
              <input type="text" id="id_fra" name="fra" class="field-input" autocomplete="off"
                     placeholder="F.eks. Kongens gate 1, 0153 Oslo"
                     value="{{ form.fra.value|default:'' }}">
              <!-- Suggestion dropdown, populated by wizard.js from ws.geonorge.no -->
              <ul class="address-suggestions" hidden></ul>
              <!-- Hidden coordinate pair — set by JS on autocomplete select / geolocation / map pin -->
              <input type="hidden" name="fra_lat" data-coord="fra_lat">
              <input type="hidden" name="fra_lon" data-coord="fra_lon">
              <!-- Mobile-only: opens the fullscreen map picker overlay -->
              <button type="button" class="map-picker-btn" data-open-map-picker="fra">
                <span data-icon="map-pin"></span>
                <span class="map-picker-btn__label">Plasser i kart</span>
              </button>
            </div>

            <div class="address-field" data-address-field="til">
              <label class="field-label" for="id_til">Til adresse</label>
              <input type="text" id="id_til" name="til" class="field-input" autocomplete="off"
                     placeholder="F.eks. Storgata 14, 0184 Oslo"
                     value="{{ form.til.value|default:'' }}">
              <ul class="address-suggestions" hidden></ul>
              <input type="hidden" name="til_lat" data-coord="til_lat">
              <input type="hidden" name="til_lon" data-coord="til_lon">
              <button type="button" class="map-picker-btn" data-open-map-picker="til">
                <span data-icon="map-pin"></span>
                <span class="map-picker-btn__label">Plasser i kart</span>
              </button>
            </div>
          </div>
        </section>

        <!-- ===================== STEP 2: type & size ===================== -->
        <section class="wizard-step" data-step="2">
          <div class="step-header">
            <h1 class="step-header__title">Hva slags flytting er det?</h1>
          </div>

          <div class="wizard-step__body">
            <div class="pill-group" data-pill-group="flytte_type">
              <p class="pill-group__label">Type</p>
              <div class="pill-group__grid pill-group__grid--3col">
                <label class="pill-button"><input type="radio" name="flytte_type" value="privat">Privat</label>
                <label class="pill-button"><input type="radio" name="flytte_type" value="bedrift">Bedrift</label>
                <label class="pill-button"><input type="radio" name="flytte_type" value="internasjonal">Internasjonal</label>
              </div>
            </div>
            <div class="pill-group" data-pill-group="boligtype">
              <p class="pill-group__label">Størrelse</p>
              <div class="pill-group__grid pill-group__grid--2col">
                <label class="pill-button"><input type="radio" name="boligtype" value="leilighet">Leilighet</label>
                <label class="pill-button"><input type="radio" name="boligtype" value="rekkehus">Rekkehus</label>
                <label class="pill-button"><input type="radio" name="boligtype" value="enebolig">Enebolig</label>
                <label class="pill-button"><input type="radio" name="boligtype" value="annet">Annet</label>
              </div>
            </div>
          </div>
        </section>

        <!-- ===================== STEP 3: date ===================== -->
        <section class="wizard-step" data-step="3">
          <div class="step-header">
            <h1 class="step-header__title">Når skal du flytte?</h1>
            <p class="step-header__subtitle">Velg en dato eller la oss vite om du er fleksibel</p>
          </div>

          <div class="wizard-step__body">
            <label class="date-field">
              <span class="field-label">Ønsket flyttedato</span>
              <input type="date" name="flyttedato" class="field-input" data-date-input>
            </label>
            <!-- Real checkbox, styled as a dashed pill — no JS needed to know its state -->
            <label class="flex-toggle" data-flex-toggle>
              <input type="checkbox" name="fleksibel" data-flex-checkbox>
              <span class="flex-toggle__dot"><span data-icon="check"></span></span>
              Jeg er fleksibel på datoen
            </label>
          </div>
        </section>

        <!-- ===================== STEP 4: goods / photos ===================== -->
        <section class="wizard-step" data-step="4">
          <div class="step-header">
            <h1 class="step-header__title">Hva skal du flytte?</h1>
            <p class="step-header__subtitle">Legg til bilder eller en beskrivelse av tingene dine.</p>
          </div>

          <div class="wizard-step__body">
            <label class="textarea-field">
              <span class="field-label field-label--strong">Beskrivelse</span>
              <textarea name="beskrivelse" rows="4" class="field-input"
                        placeholder="F.eks. 3-seters sofa, stort spisebord, 2 senger, 10 esker...">{{ form.beskrivelse.value|default:'' }}</textarea>
            </label>

            <div class="photo-field">
              <p class="field-label field-label--strong">Bilder</p>
              <p class="field-hint">Legg ved bilder av tingene dine for et mer presist tilbud.</p>
              <!-- Populated entirely by wizard.js (photo thumbnails + upload tile) -->
              <div class="photo-grid" data-photo-grid>
                <label class="photo-upload-tile">
                  <span data-icon="upload"></span>
                  <span>Last opp</span>
                  <input type="file" name="bilder" multiple accept="image/*" data-photo-input hidden>
                </label>
              </div>
            </div>
          </div>
        </section>

        <!-- ===================== STEP 5: contact ===================== -->
        <section class="wizard-step" data-step="5">
          <div class="step-header">
            <h1 class="step-header__title">La oss ta kontakt</h1>
            <p class="step-header__subtitle">Vi kobler deg med tre byråer. Du hører fra dem innen 24 timer.</p>
          </div>

          <div class="wizard-step__body wizard-step__body--grid">
            <label class="text-field">
              <span class="field-label">Navn</span>
              <input type="text" name="navn" class="field-input" placeholder="Ola Nordmann" value="{{ form.navn.value|default:'' }}">
            </label>
            <label class="text-field">
              <span class="field-label">Telefon</span>
              <input type="tel" name="telefon" class="field-input" placeholder="+47 000 00 000" value="{{ form.telefon.value|default:'' }}">
            </label>
            <label class="text-field text-field--full">
              <span class="field-label">E-post</span>
              <input type="email" name="epost" class="field-input" placeholder="ola@eksempel.no" value="{{ form.epost.value|default:'' }}">
            </label>
          </div>
        </section>

        {% if form.errors %}
        <!-- Only reachable if a client bypasses the JS validation (spec §5.11 note in Task 5) -->
        <div class="wizard-step__server-errors" role="alert">
          {{ form.non_field_errors }}
          {% for field in form %}{{ field.errors }}{% endfor %}
        </div>
        {% endif %}

        <!-- Bottom nav: back link (hidden on step 1) + primary Neste/Send button -->
        <div class="wizard-nav">
          <button type="button" class="wizard-nav__back" data-wizard-back hidden>Tilbake</button>
          <button type="button" class="wizard-nav__next btn-primary" data-wizard-next disabled>
            <span data-next-label>Neste</span>
            <span data-icon="arrow-right"></span>
          </button>
        </div>
      </div>

      <!-- RIGHT COLUMN: desktop only — map (step 1), step photo (2-4), summary (step 5) -->
      <div class="wizard-card__right">
        <!-- Step 1: live Leaflet map, built by wizard.js -->
        <!-- is-active hardcoded here (matching step 1's .wizard-step above) since
             wizard.js never calls showStep() on initial load — only on navigation,
             to avoid an unwanted slide-in animation firing on first paint. -->
        <div class="map-panel is-active" data-step-panel="1">
          <div class="map-panel__map" data-map-container></div>
          <div class="map-panel__chip" data-map-chip hidden>
            <span class="map-panel__chip-prefix">Ca.</span>
            <span data-map-chip-from>—</span>
            <span data-icon="arrow-right"></span>
            <span data-map-chip-to>—</span>
          </div>
          <div class="map-panel__zoom">
            <button type="button" class="map-panel__zoom-btn" data-map-zoom-in aria-label="Zoom inn"><span data-icon="zoom-in"></span></button>
            <button type="button" class="map-panel__zoom-btn" data-map-zoom-out aria-label="Zoom ut"><span data-icon="zoom-out"></span></button>
          </div>
          <button type="button" class="map-panel__locate" data-map-locate aria-label="Bruk min plassering" title="Bruk min plassering">
            <span data-icon="send"></span>
          </button>
          <div class="map-panel__place-toggles">
            <button type="button" class="place-pill" data-place-toggle="fra">Plasser fra</button>
            <button type="button" class="place-pill" data-place-toggle="til">Plasser til</button>
          </div>
          <div class="map-panel__attribution">
            <button type="button" class="map-panel__attribution-btn" aria-label="Kart-attribusjon"><span data-icon="info"></span></button>
            <div class="map-panel__attribution-tooltip">&copy; Leaflet &middot; &copy; CARTO &middot; &copy; OpenStreetMap</div>
          </div>
        </div>

        <!-- Steps 2-4: static lifestyle photo -->
        <div class="step-art" data-step-panel="2">
          <img src="{% static 'images/wizard/R1-07829-0034.jpg' %}" alt="">
        </div>
        <div class="step-art" data-step-panel="3">
          <img src="{% static 'images/wizard/rull3_26.jpg' %}" alt="">
        </div>
        <div class="step-art" data-step-panel="4">
          <img src="{% static 'images/wizard/R1-09476-0028.jpg' %}" alt="">
        </div>

        <!-- Step 5: live summary/receipt panel, filled in by wizard.js as fields change -->
        <div class="summary-panel" data-step-panel="5">
          <span class="summary-panel__eyebrow">Kvittering</span>
          <h3 class="summary-panel__title">Din forespørsel</h3>
          <p class="summary-panel__intro">Vi sender denne til tre kvalitetssjekkede byråer i ditt område.</p>
          <div class="summary-panel__rows" data-summary-rows>
            <!-- Rows injected by updateSummaryPanel() in wizard.js: Fra / Til / Flytting / Når / Innhold / Bilder -->
          </div>
        </div>
      </div>

    </div>
  </form>
</div>

<!-- ============================================================ -->
<!-- MOBILE MAP PICKER OVERLAY — fullscreen, opened via "Plasser i kart" -->
<!-- ============================================================ -->
<div class="map-overlay" data-map-overlay role="dialog" aria-modal="true" hidden>
  <div class="map-overlay__map" data-map-overlay-container></div>

  <div class="map-overlay__header">
    <div class="map-overlay__instruction">
      <p class="map-overlay__title" data-map-overlay-title>Hvor flytter du fra?</p>
      <p class="map-overlay__hint">Flytt kartet så nålen står på adressen din</p>
    </div>
    <button type="button" class="map-overlay__close" data-map-overlay-close aria-label="Lukk kart">
      <span data-icon="x"></span>
    </button>
  </div>

  <!-- Fixed center crosshair pin — the map pans underneath it -->
  <div class="map-overlay__pin" aria-hidden="true"><span data-icon="crosshair"></span></div>

  <button type="button" class="map-overlay__locate" data-map-overlay-locate aria-label="Bruk min posisjon">
    <span data-icon="locate-fixed"></span>
  </button>

  <div class="map-overlay__sheet">
    <p class="map-overlay__sheet-label">Valgt plassering</p>
    <p class="map-overlay__sheet-address" data-map-overlay-address>Finner adresse …</p>
    <button type="button" class="map-overlay__confirm btn-primary" data-map-overlay-confirm>
      <span data-icon="check"></span>
      Bruk denne plasseringen
    </button>
  </div>
</div>

{% include "leads/_icon_sprite.html" %}

<script>
  // Server-computed context, read once by wizard.js on load.
  window.KOBLY_WIZARD_INITIAL_CENTER = {{ initial_center_json|safe }};
  // Mobile background image per step (spec §5.3) — filenames are fixed, but the
  // URLs must come from {% static %}, so this map is built server-side and read
  // by wizard.js's mobile background crossfade logic.
  window.KOBLY_MOBILE_BACKGROUNDS = {
    1: "{% static 'images/wizard/boxes-and-plants.jpg' %}",
    2: "{% static 'images/wizard/R1-07829-0034.jpg' %}",
    3: "{% static 'images/wizard/rull3_26.jpg' %}",
    4: "{% static 'images/wizard/R1-09476-0023-kopi.jpg' %}",
    5: "{% static 'images/wizard/boxes-and-plants.jpg' %}"
  };
</script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script src="{% static 'js/wizard.js' %}"></script>
</body>
</html>
```

```html
<!-- apps/leads/templates/leads/_logo.html -->
{% comment %} Kobly wordmark: ring icon + "Kobly" text. tone="ink" (default, dark text/stroke) or "brand-ink" (light, for use on the dark mobile background). {% endcomment %}
<span class="kobly-logo kobly-logo--{{ tone }}">
  <svg width="22" height="22" viewBox="0 0 27 27" fill="none" aria-hidden="true">
    <circle cx="13.5" cy="13.5" r="11.625" stroke="currentColor" stroke-width="3.75" />
    <path d="M16.5 1.875C12.7075 5.23556 10.5 9.26144 10.5 13.5887C10.5 17.8401 12.6307 21.8006 16.3019 25.125" stroke="currentColor" stroke-width="3.75" />
  </svg>
  <span class="kobly-logo__text">Kobly</span>
</span>
```

Create the icon sprite (Task 8 also owns this — every `data-icon` reference above resolves against it):

```html
<!-- apps/leads/templates/leads/_icon_sprite.html -->
{% comment %}
One inline SVG sprite for every lucide icon the wizard uses (spec §5.14).
Referenced elsewhere as <span data-icon="x"></span> — wizard.js's
initIconSprite() clones the matching <symbol> into each placeholder on load
(see Task 10). Kept as one hidden sprite instead of repeating full <svg>
markup everywhere, but every icon here is still plain static SVG — no icon
font, no JS icon library.
{% endcomment %}
<svg style="display:none" aria-hidden="true">
  <symbol id="icon-arrow-right" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
  </symbol>
  <symbol id="icon-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M20 6 9 17l-5-5"/>
  </symbol>
  <symbol id="icon-info" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
  </symbol>
  <symbol id="icon-map-pin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>
  </symbol>
  <symbol id="icon-send" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z"/><path d="m21.854 2.147-10.94 10.939"/>
  </symbol>
  <symbol id="icon-upload" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 3v12"/><path d="m17 8-5-5-5 5"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
  </symbol>
  <symbol id="icon-x" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
  </symbol>
  <symbol id="icon-zoom-in" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/><path d="M11 8v6"/><path d="M8 11h6"/>
  </symbol>
  <symbol id="icon-zoom-out" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/><path d="M8 11h6"/>
  </symbol>
  <symbol id="icon-crosshair" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="10"/><path d="M22 12h-4"/><path d="M6 12H2"/><path d="M12 6V2"/><path d="M12 22v-4"/>
  </symbol>
  <symbol id="icon-locate-fixed" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <line x1="2" x2="5" y1="12" y2="12"/><line x1="19" x2="22" y1="12" y2="12"/><line x1="12" x2="12" y1="2" y2="5"/><line x1="12" x2="12" y1="19" y2="22"/><circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="3"/>
  </symbol>
</svg>
```

Also write the real thank-you template now (same task — small and it uses the same `_logo.html`/icon sprite include):

```html
<!-- apps/leads/templates/leads/thank_you.html -->
{% load static %}
<!DOCTYPE html>
<html lang="nb">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kobly</title>
  <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{% static 'css/wizard.css' %}">
</head>
<body>

<!-- Same background photo as the wizard, flat-darkened instead of a gradient scrim (spec §5.10) -->
<div class="thankyou">
  <div class="thankyou__background" aria-hidden="true">
    <img src="{% static 'images/wizard/boxes-and-plants.jpg' %}" alt="">
    <div class="thankyou__background-scrim"></div>
  </div>

  <div class="thankyou-card">
    <!-- Routing illustration: Kobly ring -> 3 dots -> 3 lime checkmarks, staggered pop-in -->
    <div class="thankyou-illustration">
      <span class="thankyou-illustration__logo">
        <svg width="24" height="24" viewBox="0 0 27 27" fill="none" aria-hidden="true">
          <circle cx="13.5" cy="13.5" r="11.625" stroke="currentColor" stroke-width="3.75" />
          <path d="M16.5 1.875C12.7075 5.23556 10.5 9.26144 10.5 13.5887C10.5 17.8401 12.6307 21.8006 16.3019 25.125" stroke="currentColor" stroke-width="3.75" />
        </svg>
      </span>
      <span class="thankyou-illustration__dots" aria-hidden="true">
        <span></span><span></span><span></span>
      </span>
      <span class="thankyou-illustration__checks">
        {% for delay in "120,230,340"|split:"," %}
        <span class="thankyou-illustration__check" style="animation-delay: {{ delay }}ms">
          <svg width="26" height="26" viewBox="0 0 42 42" fill="none" aria-hidden="true">
            <path d="M20.6 33.27V20.74M20.6 20.74 9.69 14.48M20.6 20.74l10.91-6.26M14.96 11.06l11.27 6.45M19.35 32.93c.38.22.81.34 1.25.34s.87-.12 1.25-.34l8.77-5.01c.38-.22.7-.54.92-.92.22-.38.34-.81.34-1.25V15.73c0-.44-.12-.87-.34-1.25-.22-.38-.54-.7-.92-.92l-8.77-5.01c-.38-.22-.81-.34-1.25-.34s-.87.12-1.25.34l-8.77 5.01c-.38.22-.7.54-.92.92-.22.38-.34.81-.34 1.25v10.02c0 .44.12.87.34 1.25.22.38.54.7.92.92l8.77 5.01Z" stroke="#3D5507" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
        {% endfor %}
      </span>
    </div>

    <h1 class="thankyou-card__title">Forespørselen er sendt!</h1>
    <p class="thankyou-card__body">Vi har nå sendt forespørselen din til tre kvalitetssjekkede byråer i ditt område. Du mottar tilbud på e-post innen kort tid.</p>
    <a href="/" class="btn-primary btn-primary--full">Tilbake til forsiden</a>
  </div>
</div>

</body>
</html>
```

Note: Django's built-in template filters don't include a `split` filter — replace that `{% for delay in "120,230,340"|split:"," %}` loop with three explicit hardcoded blocks instead (simpler and avoids adding a custom template filter for three static numbers):

```html
      <span class="thankyou-illustration__checks">
        <span class="thankyou-illustration__check" style="animation-delay: 120ms">
          <svg width="26" height="26" viewBox="0 0 42 42" fill="none" aria-hidden="true">
            <path d="M20.6 33.27V20.74M20.6 20.74 9.69 14.48M20.6 20.74l10.91-6.26M14.96 11.06l11.27 6.45M19.35 32.93c.38.22.81.34 1.25.34s.87-.12 1.25-.34l8.77-5.01c.38-.22.7-.54.92-.92.22-.38.34-.81.34-1.25V15.73c0-.44-.12-.87-.34-1.25-.22-.38-.54-.7-.92-.92l-8.77-5.01c-.38-.22-.81-.34-1.25-.34s-.87.12-1.25.34l-8.77 5.01c-.38.22-.7.54-.92.92-.22.38-.34.81-.34 1.25v10.02c0 .44.12.87.34 1.25.22.38.54.7.92.92l8.77 5.01Z" stroke="#3D5507" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
        <span class="thankyou-illustration__check" style="animation-delay: 230ms">
          <svg width="26" height="26" viewBox="0 0 42 42" fill="none" aria-hidden="true">
            <path d="M20.6 33.27V20.74M20.6 20.74 9.69 14.48M20.6 20.74l10.91-6.26M14.96 11.06l11.27 6.45M19.35 32.93c.38.22.81.34 1.25.34s.87-.12 1.25-.34l8.77-5.01c.38-.22.7-.54.92-.92.22-.38.34-.81.34-1.25V15.73c0-.44-.12-.87-.34-1.25-.22-.38-.54-.7-.92-.92l-8.77-5.01c-.38-.22-.81-.34-1.25-.34s-.87.12-1.25.34l-8.77 5.01c-.38.22-.7.54-.92.92-.22.38-.34.81-.34 1.25v10.02c0 .44.12.87.34 1.25.22.38.54.7.92.92l8.77 5.01Z" stroke="#3D5507" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
        <span class="thankyou-illustration__check" style="animation-delay: 340ms">
          <svg width="26" height="26" viewBox="0 0 42 42" fill="none" aria-hidden="true">
            <path d="M20.6 33.27V20.74M20.6 20.74 9.69 14.48M20.6 20.74l10.91-6.26M14.96 11.06l11.27 6.45M19.35 32.93c.38.22.81.34 1.25.34s.87-.12 1.25-.34l8.77-5.01c.38-.22.7-.54.92-.92.22-.38.34-.81.34-1.25V15.73c0-.44-.12-.87-.34-1.25-.22-.38-.54-.7-.92-.92l-8.77-5.01c-.38-.22-.81-.34-1.25-.34s-.87.12-1.25.34l-8.77 5.01c-.38.22-.7.54-.92.92-.22.38-.34.81-.34 1.25v10.02c0 .44.12.87.34 1.25.22.38.54.7.92.92l8.77 5.01Z" stroke="#3D5507" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
      </span>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.leads`
Expected: PASS (Note: `{% static 'css/wizard.css' %}` and `wizard.js` don't exist until Tasks 9-13 — that's fine, Django's `{% static %}` tag doesn't verify the file exists at render time, it just builds the URL, so these tests pass now and the page becomes fully styled/interactive once those tasks land.)

- [ ] **Step 5: Commit**

```bash
git add apps/leads/templates apps/leads/tests.py
git commit -m "feat: full wizard and thank-you page markup (all 5 steps)"
```

---

### Task 9: `wizard.scss` — layout, card, steps, nav, responsive breakpoints

**Files:**
- Create: `static/scss/wizard.scss`
- Create: `static/css/wizard.css` (compiled output)

**Interfaces:**
- Consumes: every token from `_kobly-tokens.scss` (Task 7) and every class name from `wizard.html` (Task 8).
- Produces: `static/css/wizard.css`, linked by both `wizard.html` and `thank_you.html`.

- [ ] **Step 1: Write the SCSS**

```scss
// static/scss/wizard.scss
//
// Styles for /wizard and its thank-you screen. Nested parent/child per
// section, one comment banner per block — read this top to bottom like a
// document, not a utility-class soup. Compile after every edit with:
//   sass static/scss/wizard.scss static/css/wizard.css --style=expanded
//
@use "kobly-tokens" as *;

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: $font-sans;
  color: $color-ink;
  @extend %kobly-font-features;
}

// ---------------------------------------------------------------
// Shared button styles (used by wizard nav, map overlay, thank-you)
// ---------------------------------------------------------------
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border: none;
  border-radius: $radius-pill;
  background: $color-brand;
  color: $color-brand-ink;
  font-family: $font-sans;
  font-size: 0.9375rem;
  font-weight: 600;
  padding: 0.75rem 1.75rem;
  cursor: pointer;
  text-decoration: none;
  transition: background-color 0.2s ease;

  &:hover { background: rgba(34, 24, 20, 0.9); }

  // Disabled state (spec §5.11: gray, no hover, no error message)
  &:disabled {
    cursor: not-allowed;
    background: rgba(26, 26, 26, 0.1);
    color: rgba(26, 26, 26, 0.3);
  }

  &--full { width: 100%; padding: 1rem 1.5rem; font-size: 1rem; }
}

.btn-text {
  background: none;
  border: none;
  color: rgba(26, 26, 26, 0.4);
  font-family: $font-sans;
  font-size: 0.875rem;
  cursor: pointer;
  transition: color 0.2s ease;
  &:hover { color: rgba(26, 26, 26, 0.7); }
}

// ---------------------------------------------------------------
// .kobly-logo — ring icon + "Kobly" wordmark, two color tones
// ---------------------------------------------------------------
.kobly-logo {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;

  &__text {
    font-size: 1.125rem;
    font-weight: 700;
    letter-spacing: -0.01em;
  }

  &--ink { color: $color-ink; }
  &--brand-ink { color: $color-brand-ink; }
}

// =================================================================
// .wizard — fullscreen root shell
// =================================================================
.wizard {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
  background: $color-bg;

  // --- Background layers ---
  &__background {
    position: absolute;
    inset: 0;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center;
    }

    &--desktop { display: none; }
    &--mobile { display: block; }
  }

  &__background-wash {
    position: absolute;
    inset: 0;
    background: rgba(244, 241, 234, 0.85); // $color-bg at 85% (spec §5.3)
  }

  &__background-scrim {
    position: absolute;
    inset: 0;
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.55) 50%, rgba(0, 0, 0, 0.7));
  }

  // Two stacked mobile background images (see Task 8 markup + Task 10 JS):
  // "prev" holds the outgoing photo underneath, "current" is the incoming one,
  // faded in via wizard-fade-in. JS un-hides/hides "prev" around the swap.
  &__background-photo {
    position: absolute;
    inset: 0;

    &--current { animation: wizard-fade-in 0.26s ease both; }
    &--prev[hidden] { display: none; }
  }

  // --- Logo placement ---
  // Both logo placements are <a> tags — reset the default link underline once here.
  &__logo {
    text-decoration: none;
  }

  &__logo--desktop {
    display: none;
    position: absolute;
    top: 1.75rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 10;
  }

  &__logo-row {
    position: relative;
    z-index: 10;
    width: 100%;
    padding: 2rem 1.5rem 0.5rem;
  }

  &__logo--mobile { display: inline-block; }
}

// =================================================================
// .wizard-card — the white card holding the form
// =================================================================
.wizard-card {
  position: relative;
  z-index: 10;
  margin: 1rem 0;
  width: calc(100% - 3rem);
  max-width: 1060px;
  border-radius: $radius-card;
  background: $color-surface-soft;
  box-shadow: $shadow-card-elevated;
  display: flex;
  flex-direction: column;

  &__body {
    display: flex;
    flex: 1;
    flex-direction: column;
  }

  // --- Left column: form content ---
  &__left {
    position: relative;
    display: flex;
    flex: 1;
    flex-direction: column;
    padding: 1.5rem 1.5rem 6rem;
  }

  // --- Right column: map / photo / summary (desktop only) ---
  &__right {
    display: none;
  }
}

// =================================================================
// .wizard-progress — 5-segment bar, "Steg X av 5" label
// =================================================================
.wizard-progress {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 1.25rem;

  &__segment {
    height: 2px;
    flex: 1;
    border-radius: $radius-pill;
    background: rgba(26, 26, 26, 0.1);
    transition: background-color 0.3s ease;

    &.is-complete { background: $color-ink; }
  }
}

.wizard-steplabel {
  font-size: 0.875rem;
  color: rgba(26, 26, 26, 0.45);
  margin-bottom: 0.875rem;
  display: block;
}

// =================================================================
// .wizard-step — one step's content; only .is-active is shown/animated
// =================================================================
.wizard-step {
  display: none;
  flex: 1;
  flex-direction: column;
  gap: 0.875rem;

  &.is-active {
    display: flex;
  }

  // Direction-based enter animation (spec §5.11: 260ms slide+fade)
  &.wizard-step--enter-right { animation: wizard-slide-in-right 0.26s ease both; }
  &.wizard-step--enter-left { animation: wizard-slide-in-left 0.26s ease both; }

  &__body {
    display: flex;
    flex-direction: column;
    gap: 0.875rem;
    margin-top: 1rem;

    &--grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 0.875rem;
    }
  }

  &__server-errors {
    color: #b3261e;
    font-size: 0.875rem;
    margin-top: 0.5rem;
  }
}

@keyframes wizard-slide-in-right {
  from { opacity: 0; transform: translateX(16px); }
  to { opacity: 1; transform: translateX(0); }
}
@keyframes wizard-slide-in-left {
  from { opacity: 0; transform: translateX(-16px); }
  to { opacity: 1; transform: translateX(0); }
}
@keyframes wizard-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

// --- .step-header — title + optional subtitle, shared by every step ---
.step-header {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;

  &__title {
    margin: 0;
    font-family: $font-serif;
    font-size: 1.875rem;
    font-weight: 500;
    line-height: 1.15;
    letter-spacing: -0.01em;
    color: $color-ink;
  }

  &__subtitle {
    margin: -0.25rem 0 0;
    font-size: 0.875rem;
    color: rgba(26, 26, 26, 0.4);
  }
}

// --- shared field primitives ---
.field-label {
  display: block;
  margin-bottom: 0.375rem;
  font-size: 0.875rem;
  color: rgba(26, 26, 26, 0.5);

  &--strong {
    font-size: 1rem;
    font-weight: 500;
    color: $color-ink;
    margin-bottom: 0.25rem;
  }
}

.field-hint {
  margin: 0 0 0.75rem;
  font-size: 0.875rem;
  color: rgba(26, 26, 26, 0.5);
}

.field-input {
  width: 100%;
  border: 1.5px solid rgba(26, 26, 26, 0.1);
  border-radius: $radius-card;
  background: #f7f5f1;
  padding: 0.875rem 1rem;
  font-size: 0.875rem;
  font-family: $font-sans;
  color: $color-ink;
  outline: none;
  transition: border-color 0.2s ease;

  &:focus { border-color: $color-brand; }
}

textarea.field-input { resize: none; }

// =================================================================
// STEP 1 — address fields + suggestion dropdown + mobile map-picker button
// =================================================================
.address-field {
  position: relative;

  .address-suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    z-index: 50;
    margin: 0.25rem 0 0;
    padding: 0;
    list-style: none;
    max-height: 18rem;
    overflow-y: auto;
    border: 1px solid rgba(26, 26, 26, 0.1);
    border-radius: $radius-card;
    background: $color-surface;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);

    li button {
      display: flex;
      width: 100%;
      flex-direction: column;
      align-items: flex-start;
      gap: 0.125rem;
      border: none;
      background: none;
      padding: 0.75rem 1rem;
      text-align: left;
      font-size: 0.875rem;
      cursor: pointer;

      &:hover { background: #f3eee3; }
    }

    .address-suggestions__meta { font-size: 0.75rem; color: rgba(26, 26, 26, 0.5); }
  }
}

// "Plasser i kart" — mobile only
.map-picker-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  min-height: 44px;
  border: none;
  border-radius: $radius-pill;
  padding: 0 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  background: rgba(26, 26, 26, 0.05);
  color: $color-ink;
  cursor: pointer;
  transition: background-color 0.2s ease;

  &:hover { background: rgba(26, 26, 26, 0.1); }

  &.is-placed {
    background: rgba(214, 232, 168, 0.4); // $color-accent-lime at 40%
  }
}

// =================================================================
// STEP 2 — pill groups (type/size selection)
// =================================================================
.pill-group {
  &__label {
    margin: 0 0 0.5rem;
    font-size: 0.875rem;
    color: rgba(26, 26, 26, 0.5);
  }

  &__grid {
    display: grid;
    gap: 0.5rem;

    &--3col { grid-template-columns: repeat(3, 1fr); }
    &--2col { grid-template-columns: repeat(2, 1fr); }
  }

  & + & { margin-top: 1.25rem; }
}

.pill-button {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: $radius-card;
  border: 1.5px solid transparent;
  background: #f3eee3;
  color: rgba(26, 26, 26, 0.6);
  padding: 1rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s ease;

  // The actual state lives on the native radio input — CSS reads :checked,
  // no JS needed to know whether a pill is selected.
  input { position: absolute; opacity: 0; pointer-events: none; }

  &:hover { background: #e8e0d0; }

  &:has(input:checked) {
    border-color: $color-brand;
    background: $color-brand;
    color: $color-brand-ink;
  }
}

// =================================================================
// STEP 3 — date field + flexible toggle
// =================================================================
.date-field {
  display: block;

  input[type="date"] {
    &:disabled { opacity: 0.5; }
  }
}

.flex-toggle {
  display: inline-flex;
  align-self: flex-start;
  align-items: center;
  gap: 0.75rem;
  border: 1.5px dashed rgba(26, 26, 26, 0.2);
  border-radius: $radius-pill;
  padding: 0.75rem 1.5rem;
  font-size: 0.875rem;
  color: rgba(26, 26, 26, 0.6);
  cursor: pointer;
  transition: border-color 0.2s ease;

  input { position: absolute; opacity: 0; pointer-events: none; }

  &__dot {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.25rem;
    height: 1.25rem;
    border-radius: 50%;
    border: 1.5px solid rgba(26, 26, 26, 0.2);

    [data-icon] { display: none; width: 0.75rem; height: 0.75rem; color: $color-brand-ink; }
  }

  &:hover { border-color: rgba(26, 26, 26, 0.4); }

  &:has(input:checked) {
    border-style: solid;
    border-color: $color-brand;
    background: #ede5d8;
    color: $color-ink;

    .flex-toggle__dot {
      border-color: $color-brand;
      background: $color-brand;
      [data-icon] { display: inline-flex; }
    }
  }
}

// =================================================================
// STEP 4 — description + photo grid
// =================================================================
.photo-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
}

.photo-thumb {
  position: relative;
  aspect-ratio: 1 / 1;
  border-radius: $radius-card;
  overflow: hidden;

  img { width: 100%; height: 100%; object-fit: cover; display: block; }

  &__remove {
    position: absolute;
    top: 0.25rem;
    right: 0.25rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.25rem;
    height: 1.25rem;
    border: none;
    border-radius: 50%;
    background: rgba(26, 26, 26, 0.7);
    color: white;
    cursor: pointer;

    [data-icon] { width: 0.75rem; height: 0.75rem; }
  }
}

.photo-upload-tile {
  display: flex;
  aspect-ratio: 1 / 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  border: 1.5px dashed rgba(26, 26, 26, 0.2);
  border-radius: $radius-card;
  background: #f7f5f1;
  color: rgba(26, 26, 26, 0.6);
  font-size: 0.75rem;
  cursor: pointer;
  transition: border-color 0.2s ease;

  &:hover { border-color: rgba(26, 26, 26, 0.4); }
}

// =================================================================
// STEP 5 — contact fields
// =================================================================
.text-field {
  display: block;
  &--full { grid-column: 1 / -1; }
}

// =================================================================
// .wizard-nav — bottom "Tilbake" / "Neste" bar
// =================================================================
.wizard-nav {
  position: absolute;
  left: 1.5rem;
  right: 1.5rem;
  bottom: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;

  &__back {
    border: none;
    background: none;
    padding: 0;
    font-family: $font-sans;
    font-size: 0.875rem;
    color: rgba(26, 26, 26, 0.4);
    cursor: pointer;
    transition: color 0.2s ease;

    &:hover { color: rgba(26, 26, 26, 0.7); }
    &[hidden] { display: none; }
  }
}

// =================================================================
// RIGHT COLUMN PANELS (desktop only, see media query below)
// =================================================================
.map-panel, .step-art, .summary-panel {
  display: none;
  position: relative;
  flex: 1;
  overflow: hidden;
  border-radius: $radius-card;
  background: $color-bg;

  &.is-active { display: flex; animation: wizard-fade-in 0.26s ease both; }
}

.step-art img { width: 100%; height: 100%; object-fit: cover; }

// --- .map-panel — Leaflet map + custom controls ---
.map-panel {
  &__map { position: absolute; inset: 0; }

  &__chip {
    position: absolute;
    top: 0.75rem;
    left: 0.75rem;
    z-index: 1000;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.95);
    padding: 0.5rem 0.75rem;
    font-size: 0.75rem;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);

    &[hidden] { display: none; }
    &-prefix { color: rgba(26, 26, 26, 0.45); }
  }

  &__zoom {
    position: absolute;
    top: 0.75rem;
    right: 0.75rem;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  &__zoom-btn, &__locate {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.25rem;
    height: 2.25rem;
    border: none;
    border-radius: 8px;
    background: $color-surface;
    color: rgba(26, 26, 26, 0.7);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
    cursor: pointer;

    &:hover { background: #f7f6f3; }
  }

  &__locate {
    position: absolute;
    bottom: 0.75rem;
    left: 0.75rem;
    z-index: 1000;

    &.is-locating { animation: wizard-pulse 1.2s ease-in-out infinite; }
  }

  &__place-toggles {
    position: absolute;
    bottom: 0.75rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
    display: flex;
    gap: 0.5rem;
  }

  &__attribution {
    position: absolute;
    bottom: 0.75rem;
    right: 0.75rem;
    z-index: 1000;

    &-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 1.5rem;
      height: 1.5rem;
      border: none;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.85);
      color: rgba(26, 26, 26, 0.6);
      cursor: pointer;
    }

    &-tooltip {
      display: none;
      position: absolute;
      bottom: 100%;
      right: 0;
      margin-bottom: 0.5rem;
      white-space: nowrap;
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.95);
      padding: 0.375rem 0.625rem;
      font-size: 11px;
      color: rgba(26, 26, 26, 0.7);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }

    &:hover &-tooltip { display: block; }
  }
}

@keyframes wizard-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

// "Plasser fra" / "Plasser til" pills on the desktop map
.place-pill {
  display: inline-flex;
  align-items: center;
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: $radius-pill;
  padding: 0.5rem 1rem;
  font-size: 0.75rem;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.95);
  color: $color-ink;
  cursor: pointer;
  white-space: nowrap;

  &:hover { background: white; }

  &.is-armed { background: $color-brand; color: $color-brand-ink; }
}

// --- .summary-panel — live receipt, step 5 only ---
.summary-panel {
  flex-direction: column;
  padding: 2rem;

  &__eyebrow { font-size: 0.875rem; color: rgba(26, 26, 26, 0.45); }
  &__title { margin: 0.5rem 0 0; font-family: $font-serif; font-size: 1.5rem; font-weight: 500; color: $color-ink; }
  &__intro { margin: 0.5rem 0 0; font-size: 0.875rem; color: rgba(26, 26, 26, 0.5); }
  &__rows { display: flex; flex-direction: column; gap: 1.25rem; margin-top: 1.75rem; }

  &__row {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;

    &-label { font-size: 0.875rem; color: rgba(26, 26, 26, 0.5); }
    &-value { font-size: 0.875rem; line-height: 1.4; color: $color-ink; }
  }
}

// =================================================================
// MOBILE MAP PICKER OVERLAY (.map-overlay)
// =================================================================
.map-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  flex-direction: column;
  background: $color-bg;
  animation: wizard-fade-in 0.26s ease both;

  &[hidden] { display: none; }

  &__map { position: absolute; inset: 0; touch-action: none; }

  &__header {
    position: relative;
    z-index: 1000;
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem 1rem 2.5rem;
    background: linear-gradient(to bottom, $color-bg, rgba(244, 241, 234, 0.95), transparent);
  }

  &__instruction {
    flex: 1;
    border-radius: $radius-card;
    background: $color-surface;
    padding: 0.75rem 1rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }

  &__title { margin: 0; font-size: 0.875rem; font-weight: 600; color: $color-ink; }
  &__hint { margin: 0.125rem 0 0; font-size: 0.875rem; color: $color-ink-muted; }

  &__close, &__locate {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.75rem;
    height: 2.75rem;
    flex-shrink: 0;
    border: none;
    border-radius: 50%;
    background: $color-surface;
    color: $color-ink;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    cursor: pointer;
  }

  &__pin {
    position: absolute;
    inset: 0;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    transform: translateY(-1rem);

    [data-icon] {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 2.75rem;
      height: 2.75rem;
      border-radius: 50%;
      border: 2px solid white;
      background: $color-brand;
      color: $color-brand-ink;
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.35);
    }
  }

  &__locate {
    position: relative;
    z-index: 1000;
    margin: auto 1rem 0.75rem auto;

    &.is-locating { animation: wizard-pulse 1.2s ease-in-out infinite; }
  }

  &__sheet {
    position: relative;
    z-index: 1000;
    background: $color-bg;
    padding: 1rem 1rem max(1rem, env(safe-area-inset-bottom));
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.08);
  }

  &__sheet-label { margin: 0; font-size: 0.75rem; color: $color-ink-muted; }
  &__sheet-address {
    margin: 0.25rem 0 0;
    min-height: 2.75rem;
    font-size: 1rem;
    font-weight: 500;
    color: $color-ink;

    &.is-loading { opacity: 0.5; }
  }
}

// =================================================================
// .thankyou — post-submit confirmation screen
// =================================================================
.thankyou {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
  padding: 2.5rem 1.5rem;
  background: $color-bg;

  &__background {
    position: absolute;
    inset: 0;
    img { width: 100%; height: 100%; object-fit: cover; }
  }

  &__background-scrim {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.65);
  }
}

.thankyou-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 520px;
  border-radius: $radius-card;
  background: $color-surface-soft;
  padding: 2.5rem 1.75rem;
  text-align: center;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
  animation: wizard-fade-in 0.26s ease both;

  &__title {
    margin: 2.25rem 0 0;
    font-family: $font-serif;
    font-size: 1.875rem;
    font-weight: 500;
    line-height: 1.1;
    color: $color-ink;
  }

  &__body {
    margin: 1rem 0 0;
    font-size: 1rem;
    line-height: 1.6;
    color: $color-ink-muted;
  }

  .btn-primary { margin-top: 2.25rem; }
}

// --- routing illustration: ring -> dots -> lime checkmarks ---
.thankyou-illustration {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;

  &__logo {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 3.5rem;
    height: 3.5rem;
    flex-shrink: 0;
    border-radius: 50%;
    background: $color-brand;
    color: $color-brand-ink;
  }

  &__dots {
    display: flex;
    align-items: center;
    gap: 0.25rem;

    span {
      width: 0.375rem;
      height: 0.375rem;
      border-radius: 50%;
      background: rgba(26, 26, 26, 0.25);
    }
  }

  &__checks {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  &__check {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 3rem;
    height: 3rem;
    border-radius: 12px;
    background: $color-accent-lime;
    opacity: 0;
    animation: wizard-pop-in 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  }
}

@keyframes wizard-pop-in {
  from { opacity: 0; transform: scale(0.6); }
  to { opacity: 1; transform: scale(1); }
}

// =================================================================
// RESPONSIVE: desktop layout kicks in at 1024px (spec §5.3)
// =================================================================
@media (min-width: 1024px) {
  .wizard {
    &__background--desktop { display: block; }
    &__background--mobile { display: none; }
    &__logo--desktop { display: block; }
    &__logo-row { display: none; }
  }

  .wizard-card {
    min-height: 640px;
    margin: 1.5rem 0;

    &__body { flex-direction: row; }
    &__left { flex: 0 0 58%; padding: 2.75rem 2.75rem 6rem; }
    &__right {
      display: flex;
      flex: 1;
      padding: 1rem 1rem 1rem 0;
    }
  }

  .wizard-nav {
    left: 2.75rem;
    right: 2.75rem;
    bottom: 1.75rem;
  }

  .map-picker-btn { display: none; } // desktop uses the right-column map instead
}

@media (min-width: 640px) and (max-width: 1023.98px) {
  .wizard-card__left { padding: 2.25rem 2.25rem 6rem; }
  .wizard-nav { left: 2.25rem; right: 2.25rem; bottom: 1.75rem; }
}
```

- [ ] **Step 2: Compile the SCSS**

Run: `sass static/scss/wizard.scss static/css/wizard.css --style=expanded`
Expected: writes `static/css/wizard.css` with no errors

- [ ] **Step 3: Verify (manual — no automated CSS test)**

Run the dev server (`python manage.py runserver`) and open `http://127.0.0.1:8000/wizard/`. Confirm: the card is centered with the soft shadow, step 1's heading renders in the serif font, the progress bar shows 5 thin segments, and the layout switches to the 2-column desktop view above 1024px width. This is a visual/manual check — CSS has no meaningful unit test.

- [ ] **Step 4: Commit**

```bash
git add static/scss/wizard.scss static/css/wizard.css
git commit -m "feat: wizard.scss — layout, steps, nav, responsive breakpoints"
```

---

### Task 10: `wizard.js` — step controller (navigation, validation gating, transitions)

**Files:**
- Create: `static/js/wizard.js`

**Interfaces:**
- Consumes: DOM structure from Task 8 (`.wizard-step[data-step]`, `[data-wizard-next]`, `[data-wizard-back]`, `.wizard-progress__segment`, `[data-current-step-label]`, `[data-icon]` + `_icon_sprite.html` symbols, `[data-step-panel]` on the right column).
- Produces: `initWizard()`, `getCurrentStep()`, `goToStep(target)`, exposed on a `window.KoblyWizard` namespace object so Tasks 11-13 (same file, added incrementally) can call into it without re-querying the DOM.

This task only handles step navigation/animation/button-gating — address autocomplete, maps, and photo upload are Tasks 11-13, appended to the same file.

- [ ] **Step 1: Write the controller**

```javascript
// static/js/wizard.js
//
// Vanilla-JS controller for the /wizard page. No framework, no build step.
// The DOM inputs are the source of truth for form data — this file only
// tracks UI-only state (current step, direction, map instances, selected
// photo files) that genuinely can't live in a plain form field.
//
// Sections, in the order they run:
//   1. Icon sprite wiring
//   2. Step navigation (this task)
//   3. Per-step validity checks (this task)
//   4. Address autocomplete (Task 11)
//   5. Maps — desktop panel + mobile picker overlay (Task 12)
//   6. Photo upload + live summary panel (Task 13)

(function () {
  "use strict";

  const TOTAL_STEPS = 5;
  let currentStep = 1;

  /**
   * Clones the matching <symbol> from the icon sprite into every not-yet-
   * hydrated [data-icon] placeholder. Idempotent on purpose — Task 13 calls
   * this again after every photo add/remove to hydrate newly created remove-
   * button icons, and re-running it must not duplicate SVGs into every icon
   * placeholder already hydrated elsewhere on the page.
   */
  function initIconSprite() {
    document.querySelectorAll("[data-icon]").forEach((el) => {
      if (el.querySelector("svg")) return; // already hydrated
      const name = el.getAttribute("data-icon");
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("width", "16");
      svg.setAttribute("height", "16");
      const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
      use.setAttribute("href", `#icon-${name}`);
      svg.appendChild(use);
      el.appendChild(svg);
    });
  }

  /** Returns true if the given step number's required fields are currently filled in correctly. */
  function isStepValid(step) {
    const form = document.querySelector(".wizard-card");
    switch (step) {
      case 1: {
        const fra = form.querySelector('[name="fra"]').value.trim();
        const til = form.querySelector('[name="til"]').value.trim();
        return fra.length > 2 && til.length > 2;
      }
      case 2: {
        const type = form.querySelector('[name="flytte_type"]:checked');
        const bolig = form.querySelector('[name="boligtype"]:checked');
        return Boolean(type) && Boolean(bolig);
      }
      case 3: {
        const date = form.querySelector('[name="flyttedato"]').value;
        const fleksibel = form.querySelector('[name="fleksibel"]').checked;
        return Boolean(date) || fleksibel;
      }
      case 4:
        return true; // always valid — goods/photos step is optional
      case 5: {
        const navn = form.querySelector('[name="navn"]').value.trim();
        const telefon = form.querySelector('[name="telefon"]').value.trim();
        const epost = form.querySelector('[name="epost"]').value.trim();
        return (
          navn.length > 1 &&
          /^[\d\s+]{8,}$/.test(telefon) &&
          /\S+@\S+\.\S+/.test(epost)
        );
      }
      default:
        return false;
    }
  }

  /** Enables/disables the Neste button based on the current step's validity, and swaps its label on step 5. */
  function updateNavButton() {
    const nextBtn = document.querySelector("[data-wizard-next]");
    const nextLabel = document.querySelector("[data-next-label]");
    nextBtn.disabled = !isStepValid(currentStep);
    nextLabel.textContent = currentStep === TOTAL_STEPS ? "Send forespørsel" : "Neste";
  }

  /** Fills in the completed segments of the 5-part progress bar and the "Steg X av 5" label. */
  function updateProgressBar() {
    document.querySelectorAll(".wizard-progress__segment").forEach((segment, index) => {
      segment.classList.toggle("is-complete", index < currentStep - 1);
    });
    document.querySelector("[data-current-step-label]").textContent = String(currentStep);
  }

  /** Shows the target step's markup and right-column panel, sliding in from the given direction. */
  function showStep(target, direction) {
    document.querySelectorAll(".wizard-step").forEach((el) => {
      const isTarget = Number(el.dataset.step) === target;
      el.classList.toggle("is-active", isTarget);
      el.classList.remove("wizard-step--enter-right", "wizard-step--enter-left");
      if (isTarget) {
        el.classList.add(direction > 0 ? "wizard-step--enter-right" : "wizard-step--enter-left");
      }
    });
    document.querySelectorAll("[data-step-panel]").forEach((el) => {
      el.classList.toggle("is-active", Number(el.dataset.stepPanel) === target);
    });
    updateMobileBackground(target);
  }

  /**
   * Crossfades the mobile-only background photo to the one mapped for `step`
   * (spec §5.3): the outgoing photo is copied into the hidden "prev" <img>
   * and revealed, the "current" <img>'s src is swapped and its fade-in
   * animation restarted, then "prev" is hidden again once the 400ms
   * crossfade finishes underneath it.
   */
  function updateMobileBackground(step) {
    const backgrounds = window.KOBLY_MOBILE_BACKGROUNDS;
    const current = document.querySelector("[data-step-bg-current]");
    const prev = document.querySelector("[data-step-bg-prev]");
    if (!backgrounds || !current || !prev) return;
    const nextUrl = backgrounds[step];
    if (!nextUrl || current.getAttribute("src") === nextUrl) return;

    prev.src = current.src;
    prev.hidden = false;

    current.src = nextUrl;
    // Restart the CSS fade-in animation by removing and re-adding its class.
    current.classList.remove("wizard__background-photo--current");
    void current.offsetWidth; // force reflow so the browser notices the class removal
    current.classList.add("wizard__background-photo--current");

    setTimeout(() => { prev.hidden = true; }, 400);
  }

  /** Navigates to an arbitrary step number, updating every dependent piece of UI. */
  function goToStep(target) {
    const direction = target > currentStep ? 1 : -1;
    currentStep = target;
    showStep(target, direction);
    updateProgressBar();
    updateNavButton();
    document.querySelector("[data-wizard-back]").hidden = currentStep === 1;
    // Task 12 hooks into step changes to lazily init the desktop map on step 1
    // and Task 13 hooks in to refresh the live summary panel on step 5 — see
    // KoblyWizard.onStepChange below.
    KoblyWizard.onStepChange.forEach((handler) => handler(currentStep));
  }

  /** Advances one step forward, or submits the form on the final step. */
  function nextStep() {
    if (!isStepValid(currentStep)) return;
    if (currentStep < TOTAL_STEPS) {
      goToStep(currentStep + 1);
    } else {
      document.querySelector(".wizard-card").submit();
    }
  }

  /** Goes back one step. No-op on step 1 (the back button is hidden there anyway). */
  function backStep() {
    if (currentStep > 1) goToStep(currentStep - 1);
  }

  /** Wires up the Neste/Tilbake buttons and re-checks validity as the user types/selects. */
  function initNavigation() {
    document.querySelector("[data-wizard-next]").addEventListener("click", nextStep);
    document.querySelector("[data-wizard-back]").addEventListener("click", backStep);
    // Re-validate on every keystroke/change anywhere in the form, cheap enough
    // for a form this size and far simpler than field-by-field listeners.
    document.querySelector(".wizard-card").addEventListener("input", updateNavButton);
    document.querySelector(".wizard-card").addEventListener("change", updateNavButton);
  }

  /**
   * Shared namespace so Tasks 11-13 (appended below in later commits) can
   * register step-change hooks and reuse goToStep without re-querying the DOM.
   */
  window.KoblyWizard = {
    goToStep,
    getCurrentStep: () => currentStep,
    onStepChange: [], // array of function(step) — populated by later sections
  };

  /** Entry point — runs everything this task owns once the DOM is ready. */
  function initWizard() {
    initIconSprite();
    initNavigation();
    updateProgressBar();
    updateNavButton();
  }

  document.addEventListener("DOMContentLoaded", initWizard);
})();
```

- [ ] **Step 2: Verify (manual — no JS test runner in this project)**

Run the dev server, open `/wizard/`, and confirm: typing 3+ characters into both address fields enables "Neste"; clicking it slides step 2 in from the right with the progress bar's first segment filled; "Tilbake" slides back from the left and hides itself on step 1; reaching step 5 changes the button label to "Send forespørsel". There is no JS test framework installed in this project (no `package.json`, no Jest/Vitest) — this is a deliberate scope boundary, not an oversight; adding one is out of scope for this plan.

- [ ] **Step 3: Commit**

```bash
git add static/js/wizard.js
git commit -m "feat: wizard.js step controller — navigation, transitions, validity gating"
```

---

### Task 11: Address autocomplete (Geonorge)

**Files:**
- Modify: `static/js/wizard.js` (append)

**Interfaces:**
- Consumes: `.address-field[data-address-field]`, `.address-suggestions`, `[data-coord]` hidden inputs (Task 8); `window.KoblyWizard` (Task 10).
- Produces: `initAddressAutocomplete()`, called from `initWizard()`.

- [ ] **Step 1: Append the autocomplete logic**

Add before the `initWizard` function definition, and add `initAddressAutocomplete();` inside `initWizard()`:

```javascript
  // ---------------------------------------------------------------
  // Address autocomplete — Kartverket's free, keyless Geonorge API
  // (spec §5.13). 200ms debounce, up to 8 results, closes 120ms after
  // blur so a click on a suggestion registers before the list vanishes.
  // ---------------------------------------------------------------

  /**
   * Calls the Geonorge address search API and returns its `adresser` array
   * (or [] on any failure, including an intentional `signal` abort — an
   * aborted request must not be treated as "no results" by its caller, so
   * callers check `signal.aborted` themselves rather than trusting an empty
   * array here to mean "user typed a query with zero matches").
   */
  async function searchAddresses(query, signal) {
    try {
      const url = `https://ws.geonorge.no/adresser/v1/sok?sok=${encodeURIComponent(query)}&treffPerSide=8&side=0`;
      const response = await fetch(url, { signal });
      if (!response.ok) return [];
      const json = await response.json();
      return json.adresser || [];
    } catch {
      return [];
    }
  }

  /** Calls the Geonorge reverse-geocode API for one coordinate; falls back to `fallbackText` on failure. */
  async function reverseGeocode(lat, lon, fallbackText) {
    try {
      const url = `https://ws.geonorge.no/adresser/v1/punktsok?radius=200&lat=${lat}&lon=${lon}&treffPerSide=1&side=0`;
      const response = await fetch(url);
      if (!response.ok) return fallbackText;
      const json = await response.json();
      const hit = (json.adresser || [])[0];
      return hit ? `${hit.adressetekst}, ${hit.postnummer} ${hit.poststed}` : fallbackText;
    } catch {
      return fallbackText;
    }
  }

  /** Renders the suggestion <li> list for one address field, wiring up click-to-select on each row. */
  function renderSuggestions(listEl, suggestions, onSelect) {
    listEl.innerHTML = "";
    if (suggestions.length === 0) {
      listEl.hidden = true;
      return;
    }
    suggestions.forEach((address) => {
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.innerHTML = `<span>${address.adressetekst}</span><span class="address-suggestions__meta">${address.postnummer} ${address.poststed}</span>`;
      // mousedown (not click) fires before the input's blur handler closes the list.
      button.addEventListener("mousedown", (event) => {
        event.preventDefault();
        onSelect(address);
      });
      li.appendChild(button);
      listEl.appendChild(li);
    });
    listEl.hidden = false;
  }

  /** Wires up debounced search + selection for one .address-field element ("fra" or "til"). */
  function initOneAddressField(fieldEl) {
    const key = fieldEl.dataset.addressField; // "fra" | "til"
    const input = fieldEl.querySelector(`[name="${key}"]`);
    const list = fieldEl.querySelector(".address-suggestions");
    const latInput = fieldEl.querySelector(`[data-coord="${key}_lat"]`);
    const lonInput = fieldEl.querySelector(`[data-coord="${key}_lon"]`);
    let debounceTimer = null;
    // Aborted on every new keystroke's search and on blur, so a slow response
    // from an earlier query can never land after a newer one (or after the
    // field lost focus) and reopen/overwrite the suggestion list.
    let abortController = null;

    const selectAddress = (address) => {
      const point = address.representasjonspunkt;
      input.value = `${address.adressetekst}, ${address.postnummer} ${address.poststed}`;
      latInput.value = point ? point.lat : "";
      lonInput.value = point ? point.lon : "";
      list.hidden = true;
      // Task 12's map reads these same hidden inputs to place/move its pin.
      KoblyWizard.onCoordChange && KoblyWizard.onCoordChange(key, point ? point.lat : null, point ? point.lon : null, input.value);
    };

    input.addEventListener("input", () => {
      // Manual typing invalidates any previously attached coordinate (spec §5.5).
      latInput.value = "";
      lonInput.value = "";
      clearTimeout(debounceTimer);
      abortController?.abort();
      const query = input.value.trim();
      if (query.length < 2) {
        list.hidden = true;
        return;
      }
      debounceTimer = setTimeout(async () => {
        abortController = new AbortController();
        const results = await searchAddresses(query, abortController.signal);
        if (abortController.signal.aborted) return;
        renderSuggestions(list, results, selectAddress);
      }, 200);
    });

    input.addEventListener("blur", () => {
      // Cancel both a pending debounce (search hasn't fired yet) and an
      // in-flight request (search already fired) — either one resolving
      // after blur must not be able to reopen the dropdown on a field
      // that's no longer focused.
      clearTimeout(debounceTimer);
      abortController?.abort();
      setTimeout(() => { list.hidden = true; }, 120);
    });

    // Exposed so Task 12's map (pin drag / click-to-place / geolocation) can
    // push a coordinate + resolved address back into this same field.
    fieldEl.setAddressFromCoord = (lat, lon, address) => {
      input.value = address;
      latInput.value = lat;
      lonInput.value = lon;
    };
  }

  /** Wires up both address fields (fra/til) on step 1. */
  function initAddressAutocomplete() {
    document.querySelectorAll(".address-field").forEach(initOneAddressField);
  }
```

- [ ] **Step 2: Verify (manual)**

On `/wizard/` step 1, type "Kongens gate" into "Fra adresse" and confirm a dropdown of real Oslo addresses appears within ~200ms, and clicking one fills the field with the full formatted address and closes the dropdown.

- [ ] **Step 3: Commit**

```bash
git add static/js/wizard.js
git commit -m "feat: wizard address autocomplete via Geonorge"
```

---

### Task 12: Maps — desktop `MapPanel` + mobile `MapPickerOverlay`

**Files:**
- Modify: `static/js/wizard.js` (append)

**Interfaces:**
- Consumes: `window.L` (Leaflet, loaded via CDN in `wizard.html`), `window.KOBLY_WIZARD_INITIAL_CENTER`, `.map-panel`, `.map-overlay` DOM (Task 8), `reverseGeocode()` (Task 11), `KoblyWizard.onStepChange`/`onCoordChange` (Task 10/11).
- Produces: `initDesktopMap()`, `initMobileMapPicker()`, both called from `initWizard()`.

- [ ] **Step 1: Append the map logic**

Add before `initWizard`, and add `initDesktopMap(); initMobileMapPicker();` inside `initWizard()`:

```javascript
  // ---------------------------------------------------------------
  // Desktop map (.map-panel) — Leaflet + free CARTO Voyager tiles.
  // Two draggable pins (from/to), a 250m circle around "from", a dashed
  // line + Kobly ring icon at the midpoint once both pins exist, and
  // "Plasser fra"/"Plasser til" click-to-place toggles (spec §5.5).
  // ---------------------------------------------------------------

  const PIN_COLOR_FROM = "#221814";
  const PIN_COLOR_TO = "#3D5507";
  const TILE_URL = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png";

  /** Builds a Leaflet divIcon: a colored circle with a white house-pin glyph, matching the reference exactly. */
  function pinIcon(color) {
    return L.divIcon({
      className: "",
      html: `<div style="width:36px;height:36px;background:${color};border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.3);border:2px solid white"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg></div>`,
      iconSize: [36, 36],
      iconAnchor: [18, 18],
    });
  }

  /** Builds the small white Kobly-ring icon shown at the midpoint of the from/to line. */
  function midpointIcon() {
    return L.divIcon({
      className: "",
      html: `<div style="width:32px;height:32px;background:white;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.18);border:1.5px solid #E6E1D6"><svg width="16" height="16" viewBox="0 0 27 27" fill="none"><circle cx="13.5" cy="13.5" r="11.625" stroke="#221814" stroke-width="3.75"/><path d="M16.5 1.875C12.7075 5.23556 10.5 9.26144 10.5 13.5887C10.5 17.8401 12.6307 21.8006 16.3019 25.125" stroke="#221814" stroke-width="3.75"/></svg></div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });
  }

  /** Builds and wires up the step-1 desktop map — a page-lifetime singleton, never destroyed/recreated. */
  function initDesktopMap() {
    const panel = document.querySelector(".map-panel");
    if (!panel || typeof L === "undefined") return;

    const initialCenter = window.KOBLY_WIZARD_INITIAL_CENTER;
    const map = L.map(panel.querySelector("[data-map-container]"), {
      center: initialCenter ? [initialCenter.lat, initialCenter.lon] : [60.5, 10.0],
      zoom: initialCenter ? initialCenter.zoom : 5,
      zoomControl: false,
      attributionControl: false,
    });
    L.tileLayer(TILE_URL, { maxZoom: 19 }).addTo(map);

    let fromMarker = null;
    let toMarker = null;
    let fromCircle = null;
    let line = null;
    let midpointMarker = null;
    let placing = null; // "fra" | "til" | null

    /** Redraws the connecting line, midpoint icon, and "from" radius circle from the two markers' current positions. */
    function redrawOverlays() {
      if (fromMarker && toMarker) {
        const a = fromMarker.getLatLng();
        const b = toMarker.getLatLng();
        const latlngs = [a, b];
        if (line) line.setLatLngs(latlngs);
        else line = L.polyline(latlngs, { color: "#221814", weight: 2.5, dashArray: "6 6", opacity: 0.7 }).addTo(map);
        const mid = [(a.lat + b.lat) / 2, (a.lng + b.lng) / 2];
        if (midpointMarker) midpointMarker.setLatLng(mid);
        else midpointMarker = L.marker(mid, { icon: midpointIcon(), interactive: false, zIndexOffset: 500 }).addTo(map);
        map.fitBounds(latlngs, { padding: [40, 40], maxZoom: 13 });
      } else {
        if (line) { line.remove(); line = null; }
        if (midpointMarker) { midpointMarker.remove(); midpointMarker = null; }
      }
      if (fromMarker) {
        const ll = fromMarker.getLatLng();
        if (fromCircle) fromCircle.setLatLng(ll);
        else fromCircle = L.circle(ll, { radius: 250, color: "#221814", fillColor: "#221814", fillOpacity: 0.08, opacity: 0.25, weight: 1, interactive: false }).addTo(map);
      } else if (fromCircle) {
        fromCircle.remove();
        fromCircle = null;
      }
      updateChip();
    }

    /**
     * Live position update for the "drag" event only — moves the line/circle/
     * midpoint to follow the pin without touching the viewport. Kept separate
     * from redrawOverlays() so dragging an already-placed pin doesn't fight
     * the user by re-fitBounds-ing the map on every mouse-move tick; the full
     * redraw (with fitBounds) still runs once, on "dragend".
     */
    function updatePositionsDuringDrag() {
      if (fromMarker && toMarker && line) {
        const a = fromMarker.getLatLng();
        const b = toMarker.getLatLng();
        line.setLatLngs([a, b]);
        if (midpointMarker) midpointMarker.setLatLng([(a.lat + b.lat) / 2, (a.lng + b.lng) / 2]);
      }
      if (fromMarker && fromCircle) {
        fromCircle.setLatLng(fromMarker.getLatLng());
      }
    }

    /** Shows/updates the "Ca. {from} -> {to}" floating chip in the top-left of the map. */
    function updateChip() {
      const chip = panel.querySelector("[data-map-chip]");
      const fraShort = document.querySelector('[name="fra"]').value.split(",")[0]?.trim();
      const tilShort = document.querySelector('[name="til"]').value.split(",")[0]?.trim();
      if (!fraShort && !tilShort) { chip.hidden = true; return; }
      chip.querySelector("[data-map-chip-from]").textContent = fraShort || "—";
      chip.querySelector("[data-map-chip-to]").textContent = tilShort || "—";
      chip.hidden = false;
    }

    /** Places or moves the "fra"/"til" pin at a coordinate, wiring up drag-to-move with reverse geocoding. */
    function setPin(which, lat, lon) {
      const color = which === "fra" ? PIN_COLOR_FROM : PIN_COLOR_TO;
      const existing = which === "fra" ? fromMarker : toMarker;
      if (existing) {
        existing.setLatLng([lat, lon]);
      } else {
        const marker = L.marker([lat, lon], { icon: pinIcon(color), draggable: true, autoPan: true }).addTo(map);
        marker.on("drag", updatePositionsDuringDrag);
        marker.on("dragend", async () => {
          const ll = marker.getLatLng();
          const address = await reverseGeocode(ll.lat, ll.lng, "Pin plassert i kart");
          applyCoordToField(which, ll.lat, ll.lng, address);
        });
        if (which === "fra") fromMarker = marker; else toMarker = marker;
      }
      redrawOverlays();
    }

    /** Writes a coordinate + resolved address into the matching address-field's inputs and repositions its pin. */
    function applyCoordToField(which, lat, lon, address) {
      const fieldEl = document.querySelector(`.address-field[data-address-field="${which}"]`);
      fieldEl.setAddressFromCoord(lat, lon, address);
      setPin(which, lat, lon);
    }

    // Address autocomplete (Task 11) reports coordinate changes here so the map stays in sync.
    KoblyWizard.onCoordChange = (which, lat, lon) => {
      const key = which === "fra" ? "fra" : "til";
      if (lat !== null && lon !== null) setPin(key, lat, lon);
    };

    // Click-to-place ("Plasser fra" / "Plasser til")
    panel.querySelectorAll("[data-place-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const which = button.dataset.placeToggle;
        placing = placing === which ? null : which;
        panel.querySelectorAll("[data-place-toggle]").forEach((b) => {
          b.classList.toggle("is-armed", b.dataset.placeToggle === placing);
          b.textContent = b.dataset.placeToggle === placing ? "Klikk på kartet" : (b.dataset.placeToggle === "fra" ? "Plasser fra" : "Plasser til");
        });
      });
    });
    map.on("click", async (event) => {
      if (!placing) return;
      const address = await reverseGeocode(event.latlng.lat, event.latlng.lng, "Pin plassert i kart");
      applyCoordToField(placing, event.latlng.lat, event.latlng.lng, address);
      placing = null;
      panel.querySelectorAll("[data-place-toggle]").forEach((b) => {
        b.classList.remove("is-armed");
        b.textContent = b.dataset.placeToggle === "fra" ? "Plasser fra" : "Plasser til";
      });
    });

    // Zoom buttons
    panel.querySelector("[data-map-zoom-in]").addEventListener("click", () => map.zoomIn());
    panel.querySelector("[data-map-zoom-out]").addEventListener("click", () => map.zoomOut());

    // "Bruk min plassering" — geolocates and places the "fra" pin
    panel.querySelector("[data-map-locate]").addEventListener("click", () => {
      if (!navigator.geolocation) return;
      const button = panel.querySelector("[data-map-locate]");
      button.classList.add("is-locating");
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          const address = await reverseGeocode(latitude, longitude, "Min posisjon");
          applyCoordToField("fra", latitude, longitude, address);
          button.classList.remove("is-locating");
        },
        () => button.classList.remove("is-locating"),
        { enableHighAccuracy: true, timeout: 8000 },
      );
    });

    // Resize fix: Leaflet needs an explicit nudge once its container becomes visible/sized.
    setTimeout(() => map.invalidateSize(), 100);
    KoblyWizard.onStepChange.push((step) => { if (step === 1) map.invalidateSize(); });
  }

  // ---------------------------------------------------------------
  // Mobile map picker overlay (.map-overlay) — fullscreen, fixed center
  // crosshair pin, user pans the map underneath it (spec §5.5 mobile).
  // ---------------------------------------------------------------
  function initMobileMapPicker() {
    const overlay = document.querySelector("[data-map-overlay]");
    if (!overlay || typeof L === "undefined") return;

    let map = null;
    let activeField = null; // "fra" | "til"
    let resolvedAddress = null;
    // Guards against a slower, earlier reverse-geocode (e.g. from a previous
    // pan) landing after a newer one and overwriting it with a stale address
    // that no longer matches the map's current center — the same race Task
    // 11 solved for address search, applied here without needing to touch
    // reverseGeocode()'s signature (Geonorge calls are cheap enough that
    // discarding a stale result is sufficient; no network-level abort needed).
    let lookupSequence = 0;

    /** Reverse-geocodes the map's current center and updates the bottom sheet's address text. */
    async function lookupCenter() {
      const addressEl = overlay.querySelector("[data-map-overlay-address]");
      addressEl.classList.add("is-loading");
      const center = map.getCenter();
      const sequence = ++lookupSequence;
      const address = await reverseGeocode(center.lat, center.lng, "Plassering valgt i kart");
      if (sequence !== lookupSequence) return; // superseded by a newer pan/lookup — discard
      resolvedAddress = address;
      addressEl.textContent = resolvedAddress;
      addressEl.classList.remove("is-loading");
    }

    /** Opens the overlay for the given field ("fra"/"til"), initializing the map centered on any existing pin. */
    function open(which) {
      activeField = which;
      overlay.hidden = false;
      overlay.querySelector("[data-map-overlay-title]").textContent =
        which === "til" ? "Hvor flytter du til?" : "Hvor flytter du fra?";
      document.body.style.overflow = "hidden";

      const latInput = document.querySelector(`[data-coord="${which}_lat"]`);
      const lonInput = document.querySelector(`[data-coord="${which}_lon"]`);
      const hasPin = latInput.value && lonInput.value;
      const start = hasPin
        ? [Number(latInput.value), Number(lonInput.value)]
        : window.KOBLY_WIZARD_INITIAL_CENTER
          ? [window.KOBLY_WIZARD_INITIAL_CENTER.lat, window.KOBLY_WIZARD_INITIAL_CENTER.lon]
          : [59.9139, 10.7522];
      const zoom = hasPin ? 16 : 14;

      map = L.map(overlay.querySelector("[data-map-overlay-container]"), {
        center: start, zoom, zoomControl: false, attributionControl: false,
      });
      L.tileLayer(TILE_URL, { maxZoom: 19 }).addTo(map);
      setTimeout(() => map.invalidateSize(), 50);
      map.on("moveend", lookupCenter);
      lookupCenter();
    }

    /** Tears down the Leaflet instance and hides the overlay. */
    function close() {
      overlay.hidden = true;
      document.body.style.overflow = "";
      if (map) { map.remove(); map = null; }
      resolvedAddress = null;
    }

    /** Confirms the map's current center as the chosen coordinate for the active field. */
    function confirm() {
      if (!map || !activeField) return;
      const center = map.getCenter();
      const fieldEl = document.querySelector(`.address-field[data-address-field="${activeField}"]`);
      fieldEl.setAddressFromCoord(center.lat, center.lng, resolvedAddress || "Plassering valgt i kart");
      document.querySelector(`[data-open-map-picker="${activeField}"]`).classList.add("is-placed");
      document.querySelector(`[data-open-map-picker="${activeField}"] .map-picker-btn__label`).textContent = "Plasseringen valgt · endre i kart";
      // Reuse the desktop map's own pin-placement path so both stay in sync.
      KoblyWizard.onCoordChange && KoblyWizard.onCoordChange(activeField, center.lat, center.lng);
      close();
    }

    document.querySelectorAll("[data-open-map-picker]").forEach((button) => {
      button.addEventListener("click", () => open(button.dataset.openMapPicker));
    });
    overlay.querySelector("[data-map-overlay-close]").addEventListener("click", close);
    overlay.querySelector("[data-map-overlay-confirm]").addEventListener("click", confirm);
    overlay.querySelector("[data-map-overlay-locate]").addEventListener("click", () => {
      if (!navigator.geolocation || !map) return;
      const button = overlay.querySelector("[data-map-overlay-locate]");
      button.classList.add("is-locating");
      navigator.geolocation.getCurrentPosition(
        (position) => {
          map.setView([position.coords.latitude, position.coords.longitude], 16);
          button.classList.remove("is-locating");
        },
        () => button.classList.remove("is-locating"),
        { enableHighAccuracy: true, timeout: 8000 },
      );
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !overlay.hidden) close();
    });
  }
```

- [ ] **Step 2: Verify (manual)**

Desktop (window ≥1024px): open `/wizard/`, confirm the map renders in the right column on step 1, clicking "Plasser fra" then clicking the map drops a dark pin and reverse-geocodes an address into the "Fra adresse" field. Resize below 1024px: confirm the "Plasser i kart" button appears under each address field, opens a fullscreen map with a fixed center crosshair, and "Bruk denne plasseringen" fills the address field and closes the overlay.

- [ ] **Step 3: Commit**

```bash
git add static/js/wizard.js
git commit -m "feat: wizard desktop map panel + mobile map picker overlay"
```

---

### Task 13: Photo upload UI + live summary panel

**Files:**
- Modify: `static/js/wizard.js` (append)

**Interfaces:**
- Consumes: `[data-photo-grid]`, `[data-photo-input]`, `.photo-upload-tile` (Task 8), `[data-summary-rows]`, `KoblyWizard.onStepChange` (Task 10).
- Produces: `initPhotoUpload()`, `updateSummaryPanel()`, both wired into `initWizard()`.

- [ ] **Step 1: Append the photo upload + summary logic**

Add before `initWizard`, and add `initPhotoUpload();` inside `initWizard()`, plus register the summary refresh:

```javascript
  // ---------------------------------------------------------------
  // Photo upload (step 4) — browsers can't append to a file input's
  // FileList directly, so we keep our own array of File objects and
  // rebuild the input's .files from it via DataTransfer on every change.
  // ---------------------------------------------------------------
  let selectedPhotos = [];

  /** Rebuilds the hidden file input's FileList from the current selectedPhotos array. */
  function syncPhotoInput() {
    const input = document.querySelector("[data-photo-input]");
    const transfer = new DataTransfer();
    selectedPhotos.forEach((file) => transfer.items.add(file));
    input.files = transfer.files;
  }

  /** Redraws the 4-column thumbnail grid (existing photos + the trailing upload tile) from selectedPhotos. */
  function renderPhotoGrid() {
    const grid = document.querySelector("[data-photo-grid]");
    const uploadTile = grid.querySelector(".photo-upload-tile");
    grid.querySelectorAll(".photo-thumb").forEach((el) => el.remove());

    selectedPhotos.forEach((file, index) => {
      const url = URL.createObjectURL(file);
      const thumb = document.createElement("div");
      thumb.className = "photo-thumb";
      thumb.innerHTML = `<img src="${url}" alt=""><button type="button" class="photo-thumb__remove" aria-label="Fjern bilde"><span data-icon="x"></span></button>`;
      thumb.querySelector(".photo-thumb__remove").addEventListener("click", () => {
        selectedPhotos.splice(index, 1);
        syncPhotoInput();
        renderPhotoGrid();
      });
      grid.insertBefore(thumb, uploadTile);
    });

    // The upload tile's icon placeholder was just re-inserted into the DOM
    // context above (it's never removed) but new [data-icon] spans in the
    // freshly-created remove buttons need their SVGs cloned in.
    initIconSprite();
  }

  /** Wires up the file input's change event to append new files to selectedPhotos (spec §5.8: "New files append to the existing array"). */
  function initPhotoUpload() {
    const input = document.querySelector("[data-photo-input]");
    if (!input) return;
    input.addEventListener("change", () => {
      selectedPhotos = selectedPhotos.concat(Array.from(input.files));
      syncPhotoInput();
      renderPhotoGrid();
    });
  }

  // ---------------------------------------------------------------
  // Live summary panel (step 5, desktop) — re-reads the form's current
  // values and re-renders the receipt rows every time anything changes.
  // ---------------------------------------------------------------
  const FLYTTE_TYPE_LABELS = { privat: "Privat flytting", bedrift: "Bedriftsflytting", internasjonal: "Internasjonal" };
  const BOLIGTYPE_LABELS = { leilighet: "Leilighet", rekkehus: "Rekkehus", enebolig: "Enebolig", annet: "Annet" };

  /** Builds one label/value row element for the summary panel. */
  function summaryRow(label, value) {
    const row = document.createElement("div");
    row.className = "summary-panel__row";
    row.innerHTML = `<span class="summary-panel__row-label">${label}</span><span class="summary-panel__row-value"></span>`;
    row.querySelector(".summary-panel__row-value").textContent = value;
    return row;
  }

  /** Reads every wizard field from the DOM and re-renders the step-5 receipt panel (Fra/Til/Flytting/Når/Innhold/Bilder). */
  function updateSummaryPanel() {
    const rows = document.querySelector("[data-summary-rows]");
    if (!rows) return;
    const form = document.querySelector(".wizard-card");
    rows.innerHTML = "";

    const fra = form.querySelector('[name="fra"]').value.trim();
    const til = form.querySelector('[name="til"]').value.trim();
    const flytteType = form.querySelector('[name="flytte_type"]:checked');
    const boligtype = form.querySelector('[name="boligtype"]:checked');
    const dato = form.querySelector('[name="flyttedato"]').value;
    const fleksibel = form.querySelector('[name="fleksibel"]').checked;
    const beskrivelse = form.querySelector('[name="beskrivelse"]').value.trim();

    if (fra) rows.appendChild(summaryRow("Fra", fra));
    if (til) rows.appendChild(summaryRow("Til", til));
    if (flytteType || boligtype) {
      const parts = [flytteType && FLYTTE_TYPE_LABELS[flytteType.value], boligtype && BOLIGTYPE_LABELS[boligtype.value]].filter(Boolean);
      rows.appendChild(summaryRow("Flytting", parts.join(" · ")));
    }
    if (dato || fleksibel) {
      const value = fleksibel ? "Fleksibel dato" : new Date(dato).toLocaleDateString("no-NO", { day: "numeric", month: "long", year: "numeric" });
      rows.appendChild(summaryRow("Når", value));
    }
    if (beskrivelse) rows.appendChild(summaryRow("Innhold", beskrivelse));
    if (selectedPhotos.length > 0) {
      const label = document.createElement("span");
      label.className = "summary-panel__row-label";
      label.textContent = "Bilder";
      const grid = document.createElement("div");
      grid.className = "photo-grid";
      selectedPhotos.forEach((file) => {
        const thumb = document.createElement("div");
        thumb.className = "photo-thumb";
        thumb.innerHTML = `<img src="${URL.createObjectURL(file)}" alt="">`;
        grid.appendChild(thumb);
      });
      const wrapper = document.createElement("div");
      wrapper.className = "summary-panel__row";
      wrapper.appendChild(label);
      wrapper.appendChild(grid);
      rows.appendChild(wrapper);
    }
  }
```

Wire the summary refresh into navigation/input events — modify the `initNavigation` function from Task 10 by adding one line, and register a step-change hook. In `initWizard`, after `initPhotoUpload();`, add:

```javascript
    KoblyWizard.onStepChange.push((step) => { if (step === 5) updateSummaryPanel(); });
    document.querySelector(".wizard-card").addEventListener("input", updateSummaryPanel);
    document.querySelector(".wizard-card").addEventListener("change", updateSummaryPanel);
```

- [ ] **Step 2: Verify (manual)**

On step 4, click "Last opp", select 2 images, confirm both thumbnails appear with a working "×" remove button, and that clicking upload again *adds* to the existing set rather than replacing it. Advance to step 5 (desktop width) and confirm the right-column receipt shows every filled-in field, including the photo thumbnails, and updates live if you go back and change something.

- [ ] **Step 3: Commit**

```bash
git add static/js/wizard.js
git commit -m "feat: wizard photo upload (append/remove) and live step-5 summary panel"
```

---

### Task 14: End-to-end verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `python manage.py test apps.leads`
Expected: PASS — every test from Tasks 1-8 (model, form, view, template).

- [ ] **Step 2: Manual full-flow walkthrough**

Run: `python manage.py runserver`, then in a browser:

1. Open `http://127.0.0.1:8000/wizard/?by=bergen` — confirm the desktop map opens centered on Bergen, not the default Norway view.
2. Open `http://127.0.0.1:8000/wizard/?fra=1170` — confirm "Fra adresse" is pre-filled with the literal text "1170" (spec §4.4's documented low-fidelity behavior, preserved on purpose).
3. Complete all 5 steps with real data (address autocomplete, type/size pills, a flexible date, one uploaded photo, contact info) and submit.
4. Confirm you land on `/wizard/takk/` with the "Forespørselen er sendt!" screen and the routing illustration's checkmarks pop in staggered.
5. In the terminal running `runserver`, confirm the receipt email printed to the console (via `EMAIL_BACKEND`), addressed to the submitted e-post, containing the reference number and every submitted field.
6. Open `http://127.0.0.1:8000/admin/` (create a superuser first if needed: `python manage.py createsuperuser`), confirm the new `MoveLead` appears under Leads with the uploaded photo attached as an inline `LeadImage`.

- [ ] **Step 3: Report results**

No commit for this task — if everything in Step 2 passes, Phase 1 (the wizard) is complete per spec §1/§16's stated priority. If anything fails, fix it as a follow-up commit against the relevant earlier task before considering this plan done.
