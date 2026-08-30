import json
import logging
import uuid

from django.shortcuts import redirect, render
from PIL import Image

from .cities import CITIES
from .emails import send_receipt_email
from .forms import WizardForm
from .models import LeadImage, MoveLead
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
            lead = MoveLead.objects.create(**form.cleaned_data)

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
                matched_businesses = find_matching_businesses(lead.fra, lead.til, lead.flytte_type)
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
    }
    return render(request, "leads/wizard.html", context)


def wizard_thank_you(request):
    """Static thank-you screen shown after a successful submit (spec §5.10)."""
    return render(request, "leads/thank_you.html")
