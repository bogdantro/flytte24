import json
import logging
import re
import uuid
from urllib.parse import urlencode

import requests
from django.shortcuts import redirect, render
from PIL import Image

from .cities import CITIES
from .duplicates import find_double_submit, find_recent_lead
from .emails import send_receipt_email
from .forms import WizardForm
from .models import LeadImage, MoveLead, PropertyLookup

# Wizard fields that belong to step 2's property lookup, not to MoveLead —
# popped out of cleaned_data before MoveLead.objects.create(**...).
PROPERTY_FORM_FIELDS = (
    "property_token", "selected_unit", "bolig_type_manuell",
    "bolig_bra_manuell", "bolig_etasjer_manuell", "bolig_enhet_manuell",
)
from apps.store.services import (
    find_matching_businesses, notify_business_of_assignment, record_business_assignment,
)

logger = logging.getLogger(__name__)

MAX_PHOTOS = 20
MAX_PHOTO_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
# Every accepted photo is re-saved under a random name with one of these
# extensions (matching Pillow's own detected format, never the extension the
# upload arrived with) — an attacker-chosen name/extension (e.g. "x.html"
# wrapping a JPEG-polyglot payload that still parses as a valid image) must
# never survive into storage, since media/ is served from the site's own
# origin and a same-origin .html file would run as a same-origin page.
PHOTO_FORMAT_EXTENSIONS = {"JPEG": "jpg", "PNG": "png", "GIF": "gif", "WEBP": "webp"}


def _detect_photo_format(f):
    """Returns the Pillow-detected image format ("JPEG"/"PNG"/...) for an uploaded file, or None if it isn't a real, decodable image Pillow recognizes — never trusts the filename or the browser-supplied Content-Type. Restores the file's read position before returning either way."""
    try:
        f.seek(0)
        image = Image.open(f)
        image.verify()
        # verify() leaves the Image object unusable for anything further —
        # Pillow's own documented pattern is to re-open for a real read.
        f.seek(0)
        image_format = Image.open(f).format
    except Exception:
        # Deliberately broad: a corrupt file, a decompression-bomb header, or
        # any other malformed input should fail validation, not crash the
        # request — this is untrusted public input, fail closed.
        return None
    finally:
        f.seek(0)
    return image_format


def _validate_photos(files):
    """Returns a list of Norwegian error strings for any file that's too large, over the count cap, or not a real, supported-format image — server-side, since accept="image/*" is a client-side hint only."""
    errors = []
    if len(files) > MAX_PHOTOS:
        errors.append(f"Du kan laste opp maks {MAX_PHOTOS} bilder.")
        return errors
    for f in files:
        if f.size > MAX_PHOTO_SIZE_BYTES:
            errors.append(f"{f.name} er for stort (maks 10 MB per bilde).")
            continue
        image_format = _detect_photo_format(f)
        if image_format not in PHOTO_FORMAT_EXTENSIONS:
            errors.append(f"{f.name} er ikke et gyldig bilde.")
    return errors


_PROPERTY_LEAD_FIELDS = [
    "property_lookup", "bolig_adresse", "bolig_type", "bolig_bra_m2",
    "bolig_byggeaar", "bolig_etasjer", "bolig_enhet", "bolig_datakilde",
    "bolig_gnr", "bolig_bnr",
]


def _apply_property_to_lead(lead, property_data):
    """Resolve step 2's property inputs onto an already-saved MoveLead.

    Trust model: `property_token` is the only identifier we act on — the row is
    reloaded from the DB and `selected_unit` is validated against its stored
    units. The *_manuell fields are the customer's own corrections/fallback and
    win over registry values where filled in; any manual value flips
    bolig_datakilde (and the PropertyLookup) to "user".
    """
    token = (property_data.get("property_token") or "").strip()
    manual = {
        "bolig_type": (property_data.get("bolig_type_manuell") or "").strip()[:100],
        "bolig_bra_m2": property_data.get("bolig_bra_manuell"),
        "bolig_etasjer": property_data.get("bolig_etasjer_manuell"),
        "bolig_enhet": (property_data.get("bolig_enhet_manuell") or "").strip()[:20],
    }
    has_manual = any(value not in (None, "") for value in manual.values())

    lookup = PropertyLookup.objects.filter(token=token).first() if token else None

    if lookup:
        normalized = lookup.normalized or {}
        address = normalized.get("address") or {}
        building = normalized.get("building") or {}
        prop = normalized.get("property") or {}
        units = normalized.get("units") or []

        selected = (property_data.get("selected_unit") or "").strip()
        unit = next((u for u in units if u.get("unit_number") == selected), None) if selected else None

        lead.property_lookup = lookup
        lead.bolig_adresse = address.get("formatted") or ""
        lead.bolig_type = building.get("building_type") or ""
        lead.bolig_bra_m2 = (unit or {}).get("bra_m2") or building.get("bra_m2")
        lead.bolig_byggeaar = building.get("construction_year")
        lead.bolig_etasjer = building.get("number_of_floors")
        lead.bolig_enhet = (unit or {}).get("unit_number") or ""
        lead.bolig_gnr = prop.get("gnr") or ""
        lead.bolig_bnr = prop.get("bnr") or ""
        lead.bolig_datakilde = "api"

        if unit and lookup.selected_unit_number != selected:
            lookup.selected_unit_number = selected
            lookup.save(update_fields=["selected_unit_number"])

    if has_manual:
        if manual["bolig_type"]:
            lead.bolig_type = manual["bolig_type"]
        if manual["bolig_bra_m2"] is not None:
            lead.bolig_bra_m2 = manual["bolig_bra_m2"]
        if manual["bolig_etasjer"] is not None:
            lead.bolig_etasjer = manual["bolig_etasjer"]
        if manual["bolig_enhet"]:
            lead.bolig_enhet = manual["bolig_enhet"]
        lead.bolig_datakilde = "user"
        if not lead.bolig_adresse:
            lead.bolig_adresse = lead.fra[:255]
        if lookup:
            lookup.data_source = "user"
            lookup.manual_overrides = {
                key: value for key, value in manual.items() if value not in (None, "")
            }
            lookup.save(update_fields=["data_source", "manual_overrides"])

    if lookup or has_manual:
        lead.save(update_fields=_PROPERTY_LEAD_FIELDS)


def wizard(request):
    """
    Renders the 5-step lead-capture wizard (GET) and processes the final
    submission (POST).

    GET: shows an empty form, optionally pre-filled from the query string —
    ?fra=<text> drops straight into the free-text "Fra adresse" field with
    no lookup (spec §4.4 note: this low-fidelity behavior is preserved on
    purpose, matching the reference exactly) and ?by=<city slug> centers the
    map before the user has typed anything (spec §5.1/§7).

    POST: validates the form and the uploaded photos — on success, creates
    the MoveLead and any uploaded LeadImages, sends the receipt email (a
    failure there is logged but never blocks the redirect, since the lead
    is already saved by that point), and redirects to the thank-you page.
    """
    photo_errors = []
    if request.method == "POST":
        form = WizardForm(request.POST)
        photo_files = request.FILES.getlist("bilder")
        photo_errors = _validate_photos(photo_files)
        if form.is_valid() and not photo_errors:
            lead_data = dict(form.cleaned_data)
            property_data = {key: lead_data.pop(key) for key in PROPERTY_FORM_FIELDS}
            duplicate_confirmed = lead_data.pop("bekreft_duplikat", False)

            telefon = lead_data.get("telefon", "")
            epost = lead_data.get("epost", "")

            # (a) Accidental double-submit (double-click, back-button resubmit):
            # an identical lead seconds ago — just send them to the receipt,
            # don't create a second row.
            recent_identical = find_double_submit(telefon, epost)
            if recent_identical is not None:
                logger.info("Wizard: treating submission as a double-submit of %s", recent_identical.reference)
                return redirect("leads:wizard_thank_you")

            # (b) Deliberate repeat within the 7-day window. Block unless the
            # customer explicitly confirmed on the (re-rendered) contact step.
            recent_lead = find_recent_lead(telefon, epost)
            if recent_lead is not None and not duplicate_confirmed:
                context = {
                    "form": form,
                    "photo_errors": photo_errors,
                    "initial_center_json": json.dumps(None),
                    "duplicate_warning": {
                        "reference": recent_lead.reference,
                        "since": recent_lead.created_at,
                    },
                }
                return render(request, "leads/wizard.html", context)

            lead = MoveLead.objects.create(**lead_data)

            if recent_lead is not None:
                # Confirmed repeat — flag it and make sure the auto-assign block
                # below leaves it for a staff member.
                lead.is_duplicate = True
                lead.duplicate_of = recent_lead
                lead.save(update_fields=["is_duplicate", "duplicate_of"])
                logger.info(
                    "Wizard: lead %s flagged as duplicate of %s (manual assignment required)",
                    lead.reference, recent_lead.reference,
                )
            # Property/building info (step 2) — never blocks; a bad token or
            # missing lookup just leaves the bolig_* fields blank.
            try:
                _apply_property_to_lead(lead, property_data)
            except Exception:
                logger.exception("Failed to attach property lookup to lead %s", lead.reference)

            # Automatic assignment — matches the receipt email's own promise
            # ("vi matcher deg med 3 kvalitetssjekkede byråer") which, before
            # this, wasn't backed by anything: a lead just sat unassigned
            # until a staff member picked it up by hand from the dashboard.
            # Same city/service-type heuristic the dashboard's manual
            # "Tildel til bedrifter" screen uses for its own recommendations
            # (apps.store.services.business_matches_move) — fewer than 3
            # matches just means fewer than 3 assigned; staff can still fill
            # in the rest manually from the lead's detail page.
            #
            # The whole block is defensive: the MoveLead row above is already
            # committed by this point, so a bug in matching/notification must
            # never turn an already-saved lead into a 500 for the customer
            # (who'd then likely resubmit, creating a duplicate MoveLead).
            try:
                matched_businesses = [] if lead.is_duplicate else find_matching_businesses(
                    lead.fra, lead.til, lead.flytte_type
                )
                if matched_businesses:
                    for field, business in zip(("business_1", "business_2", "business_3"), matched_businesses):
                        setattr(lead, field, business)
                    lead.save(update_fields=["business_1", "business_2", "business_3"][: len(matched_businesses)])
                    for business in matched_businesses:
                        record_business_assignment(business)
                        try:
                            notify_business_of_assignment(business, lead)
                        except Exception:
                            logger.exception("Failed to notify business %s of lead %s", business.pk, lead.reference)
            except Exception:
                logger.exception("Failed to auto-assign lead %s to matching businesses", lead.reference)

            for uploaded_file in photo_files:
                # Re-detect format (cheap, and avoids trusting anything cached
                # from validation) and rename to a random filename with a
                # matching extension — never the attacker-supplied name.
                image_format = _detect_photo_format(uploaded_file)
                ext = PHOTO_FORMAT_EXTENSIONS.get(image_format, "jpg")
                uploaded_file.name = f"{uuid.uuid4().hex}.{ext}"
                LeadImage.objects.create(lead=lead, image=uploaded_file)
            try:
                send_receipt_email(lead)
            except Exception:
                logger.exception("Failed to send receipt email for lead %s", lead.reference)
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
        "photo_errors": photo_errors,
        "initial_center_json": json.dumps(initial_center),
        "duplicate_warning": None,
    }
    return render(request, "leads/wizard.html", context)


def wizard_thank_you(request):
    """Static thank-you screen shown after a successful submit (spec §5.10)."""
    return render(request, "leads/thank_you.html")


POSTAL_CODE_LOOKUP_TIMEOUT_SECONDS = 3


def start_from_postal_code(request, postal_code):
    """Redirects the homepage's "Ditt postnummer" quick-entry box into the
    wizard, pre-filling "Fra adresse" with the postal code's real area name
    when it can be resolved, rather than the bare digits.

    Regression note / spec §4.4, §15 "known quirk": the reference site's
    PostnummerInput just does `router.push('/wizard?fra=' + value)` — a user
    who types "1170" lands on step 1 with the literal text "1170" sitting in
    the free-text address field, never resolved to a real place at all. The
    spec explicitly flags this as worth a deliberate decision rather than
    silent copying: "use it as an opportunity to actually resolve the
    postcode server-side in Django." This view is that resolution — it
    looks the code up against Kartverket's free, keyless address registry
    (the same ws.geonorge.no API the wizard's own client-side address
    autocomplete already calls, per spec §5.13) and redirects into the
    wizard with "<code> <poststed>" (e.g. "1170 Oslo") when a match is
    found.

    Never blocks or 500s on the postal code itself: an invalid 4-digit
    check happens client-side already (site.js), but a malformed value
    reaching this view server-side, an API timeout, or zero results all
    fall back to the old bare-digit behavior rather than erroring — a
    slightly-worse prefill beats a broken homepage button.
    """
    fra_value = postal_code
    if re.fullmatch(r"\d{4}", postal_code):
        try:
            response = requests.get(
                "https://ws.geonorge.no/adresser/v1/sok",
                params={"postnummer": postal_code, "treffPerSide": 1},
                timeout=POSTAL_CODE_LOOKUP_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            hits = response.json().get("adresser", [])
            if hits:
                poststed = hits[0].get("poststed")
                if poststed:
                    fra_value = f"{postal_code} {poststed.title()}"
        except (requests.RequestException, ValueError):
            # ValueError covers response.json() on a non-JSON body — the
            # public API being briefly down or slow must never break this
            # button, only degrade it back to the old bare-digit behavior.
            logger.warning("Postal code lookup failed for %s; falling back to bare digits", postal_code)

    return redirect(f"/flytteforesporsel/?{urlencode({'fra': fra_value})}")
