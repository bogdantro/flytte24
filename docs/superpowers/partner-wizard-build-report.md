# Business-partner signup wizard — build report

**Date:** 2026-08-24
**Scope:** Rebuild `/for-bedrifter/bli-partner/` (`apps.core.views.for_business_partner`) as a
4-step wizard, visually and mechanically identical to the customer lead wizard at
`/flytteforesporsel/` (`apps.leads`), reusing `static/scss/wizard.css` unmodified.

## Summary

The page previously rendered a blank template stub and its view returned `JsonResponse` for an
AJAX submit no JS on the page ever called (`@csrf_exempt`, reading `request.POST.getlist("moveType")`
etc. — camelCase keys nothing ever sent). It's now a real 4-step wizard built from the same
`wizard.css` classes as the customer wizard, driven by a new `static/js/partner-wizard.js`, backed
by a new `PartnerWizardForm`, and submitted as a normal `<form method="post">` → 302 redirect.

## Files changed (commit `36494e52`)

- `apps/core/forms.py` — added `PartnerWizardForm` (new `MOVE_TYPE_CHOICES`/`CITY_CHOICES` module
  constants, `POSTNUMMER_PATTERN`). Left the pre-existing `FlytteforesporselForm` untouched.
- `apps/core/views.py` — replaced `for_business_partner`'s body. Removed `@csrf_exempt` and the
  now-unused local `JsonResponse`/`csrf_exempt` imports for this view (both symbols are still
  imported/used by other views in the same file, so only this view's redundant re-imports and
  decorator were removed). Added `from apps.store.models import PublicBusinessInformation`.
- `apps/core/templates/pages/about/for-business-partner.html` — full 4-step wizard markup
  (previously `{% extends 'core/base.html' %}{% block content %}{% endblock %}`).
- `apps/core/templates/core/_icon_sprite.html` — added `icon-arrow-left`, `icon-check`,
  `icon-upload` symbols (same `<path>` data as `apps/leads/templates/leads/_icon_sprite.html`'s
  copies). Only `icon-upload` ends up used on this specific page; `icon-x` and `icon-arrow-right`
  were already present in core's sprite. The other two are kept for parity/future reuse, per the
  instruction to add whatever's missing "following its existing icon style" — they're inert,
  zero-cost `<symbol>` defs inside a `display:none` sprite.
- `static/js/partner-wizard.js` — new file. Ported wizard.js's generic step-controller
  (`initNavigation`/`goToStep`/`showStep`/`updateProgressBar`/`updateNavButton`/`isStepValid`
  switch) and its photo-upload preview technique, trimmed to a single logo file (replace-not-append,
  upload tile hides itself once a logo is selected). Did **not** port the address-autocomplete,
  Leaflet map, or custom date-picker code — none of those fields exist on this form.
- `static/scss/wizard.css` — **not modified.** Every step's markup fit existing classes
  (`.wizard-card`, `.wizard-progress`, `.wizard-step`, `.step-header`, `.field-label`/`.field-input`,
  `.pill-group`/`.pill-button` — checkboxes reuse the same `:has(input:checked)` pill styling as the
  reference's radio pills — `.photo-upload-tile`/`.photo-thumb`/`.photo-grid`, `.text-field`,
  `.wizard-nav`, `.btn-primary`, `.step-art`). No new class was needed.

## Design decisions / deviations from the reference wizard

- **Template structure:** extends `core/base.html` (`{% block head %}` for the `wizard.css` link,
  `{% block header %}{% endblock %}`/`{% block footer %}{% endblock %}` left empty) rather than
  being a fully standalone HTML document like `leads/wizard.html`. `.wizard` is
  `position: fixed; inset: 0; z-index: 50` regardless of its DOM ancestor, so this still renders as
  the same fullscreen takeover — emptying header/footer keeps the DOM (and tab order) clean instead
  of leaving invisible nav/footer markup behind the overlay, and it means core's own
  `_icon_sprite.html` (already included once by `base.html`) and its favicon/font `<link>`s are
  reused for free instead of duplicated.
- **No mobile background-photo crossfade, no map, no date-picker, no address autocomplete** — per
  the brief, none of this form's fields need them, and the brief explicitly said simpler is fine
  here.
- **Right column (desktop):** kept `.wizard-card__right` with one static `.step-art` photo per step
  (reusing the same 4 images `leads/wizard.html` already ships — `boxes-and-plants.jpg`,
  `R1-07829-0034.jpg`, `rull3_26.jpg`, `R1-09476-0028.jpg` — no new asset weight). This wasn't in the
  explicit exclusion list (only map/date-picker/address-autocomplete panels and the crossfade were
  called out), and omitting it entirely would have left a blank 42%-width gap on desktop because
  `.wizard-card__left { flex: 0 0 58% }` is baked into `wizard.css` regardless of whether a right
  column exists — reusing `.step-art` closes that gap with zero new CSS.
- **Logo tile:** reuses `.photo-grid`/`.photo-upload-tile`/`.photo-thumb` from the reference's
  multi-photo pattern, restricted in JS to one file: selecting a new file *replaces* the current
  selection (not appends), and the upload tile hides itself once a logo is chosen, reappearing if
  removed via the same `.photo-thumb__remove` button pattern.
- **Pill groups:** step 1 (services) and step 2 (cities) use `type="checkbox"` inside the same
  `.pill-button` markup the reference uses for `type="radio"` — `.pill-button`'s `:has(input:checked)`
  selector works identically for both input types, confirmed visually via the live verification pass.
- **Norwegian copy:** step titles/subtitles and the final button label ("Send søknad", vs. the
  customer wizard's "Send forespørsel") are new copy — nothing in the brief specified exact
  wording beyond the four step headings.

## Backend

`PartnerWizardForm` (in `apps/core/forms.py`) is a plain `forms.Form`, not a `ModelForm`, per the
brief — `move_type`/`cities` are `MultipleChoiceField`s (choices = the 8 services / 5 cities) and
get joined with `", "` only at save time in the view, matching `Bedrift_info.move_type`/`.cities`'s
comma-separated `CharField` convention. Required: `company_name`, `address`, `postal_code`, `city`,
`first_name`, `last_name`, `email`, `phone`, plus at least one `move_type` and one `cities` value.
Optional: `company_number`, `employees`, `website`, `tiltaleform`, `logo` (`ImageField`).
`clean_postal_code` enforces exactly 4 digits. Error messages follow `apps.leads.forms.WizardForm`'s
convention (`clean_*` methods, Norwegian text).

`for_business_partner` (in `apps/core/views.py`): GET renders an unbound form. POST validates via
`PartnerWizardForm(request.POST, request.FILES)`; on success creates the `Bedrift_info` row (joined
`move_type`/`cities`, `user` left `None` — linked later via `/reg/fullfor/lag-bruker/`, untouched by
this view) and a linked `PublicBusinessInformation` row (`logo=form.cleaned_data["logo"]`, which is
`None`/falsy when no file was uploaded — `ImageField(blank=True, null=True)` accepts that), then
`redirect(f"/reg/fullfor/lag-bruker/?email={company.email}")` — a real 302, not `JsonResponse`. On
invalid POST, falls through to re-render the same template with the bound form (errors + entered
values persist), mirroring `apps.leads.views.wizard`'s pattern. The stray `@csrf_exempt` from the
old JSON version was removed; the form now depends on the real `{% csrf_token %}` Django renders.

## Verification

1. **`manage.py test apps.core -v 2`** — 30/30 green (24 pre-existing + 6 new
   `ForBusinessPartnerWizardTests`: GET shows all four step headings; valid POST creates
   `Bedrift_info` with correctly joined `move_type`/`cities`; valid POST creates a linked
   `PublicBusinessInformation`; POST with a logo attaches it to `PublicBusinessInformation.logo`;
   POST missing `company_name` creates no `Bedrift_info` and re-renders 200; redirect target matches
   `/reg/fullfor/lag-bruker/?email=<email>`).
2. **`manage.py test apps.pages apps.dashboard apps.leads apps.store apps.userprofile -v 0`** —
   112/112 green, nothing else broken.
3. **Live verification** — started `manage.py runserver` on `127.0.0.1:8765`:
   - `GET /for-bedrifter/bli-partner/` → 200; response body contains all four step headings, the
     `scss/wizard.css` `<link>`, the `js/partner-wizard.js` `<script>` tag, and a real
     `csrfmiddlewaretoken`.
   - Extracted the CSRF token from that GET response, sent it back as both the `csrftoken` cookie
     (via curl's cookie jar) and the `csrfmiddlewaretoken` POST field, with a real Pillow-generated
     JPEG for `logo` — `POST /for-bedrifter/bli-partner/` → **302**, `Location:
     /reg/fullfor/lag-bruker/?email=kari@livetest.no`.
   - Confirmed in the DB: `Bedrift_info` row created with `move_type="Flyttehjelp, Pakking"`,
     `cities="Oslo, Bergen"`, matching address/postal/city/tiltaleform/name/phone; linked
     `PublicBusinessInformation` row created with `logo.name == "business_logos/test_logo.jpg"`.
   - Cleaned up the test row (and its uploaded logo file) and stopped the dev server afterward —
     no test data or stray files left behind.

## Scope discipline

`git status` at the start of this session showed substantial unrelated pre-existing uncommitted
work in the tree (deleted `static/css/*`, modified `apps/leads/templates/leads/*.html`,
`static/js/wizard.js`, `static/scss/{base.css.map,dashboard.css,wizard.scss}`, a deleted
`static/scss/site.scss`, and a large number of untracked directories/files —
`.vscode/`, `app/`, `business_images/`, `business_logos/`, `components/`, `docs/`, `lib/`,
`public/`, PDFs, `static/scss/site.css*`, `static/scss/wizard.css*`, `README.txt`). None of it was
touched, staged, or committed. Only the six files listed above were `git add`ed and committed
(commit `36494e52`); everything else in the working tree remains exactly as it was.
