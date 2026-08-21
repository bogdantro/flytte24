import json
import logging

from django.shortcuts import redirect, render
from PIL import Image, UnidentifiedImageError

from .cities import CITIES
from .emails import send_receipt_email
from .forms import WizardForm
from .models import LeadImage, MoveLead

logger = logging.getLogger(__name__)

MAX_PHOTOS = 20
MAX_PHOTO_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _validate_photos(files):
    """Returns a list of Norwegian error strings for any file that's too large, over the count cap, or not a real decodable image — server-side, since accept="image/*" is a client-side hint only."""
    errors = []
    if len(files) > MAX_PHOTOS:
        errors.append(f"Du kan laste opp maks {MAX_PHOTOS} bilder.")
        return errors
    for f in files:
        if f.size > MAX_PHOTO_SIZE_BYTES:
            errors.append(f"{f.name} er for stort (maks 10 MB per bilde).")
            continue
        try:
            f.seek(0)
            Image.open(f).verify()
            f.seek(0)
        except (UnidentifiedImageError, OSError):
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
            for uploaded_file in photo_files:
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
