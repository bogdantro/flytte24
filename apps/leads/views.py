import json

from django.shortcuts import redirect, render

from .cities import CITIES
from .emails import send_receipt_email
from .forms import WizardForm
from .models import LeadImage, MoveLead


def wizard(request):
    """
    Renders the 5-step lead-capture wizard (GET) and processes the final
    submission (POST).

    GET: shows an empty form, optionally pre-filled from the query string —
    ?fra=<text> drops straight into the free-text "Fra adresse" field with
    no lookup (spec §4.4 note: this low-fidelity behavior is preserved on
    purpose, matching the reference exactly) and ?by=<city slug> centers the
    map before the user has typed anything (spec §5.1/§7).

    POST: validates and saves the lead — on success, creates the MoveLead
    and any uploaded LeadImages, sends the receipt email, and redirects to
    the thank-you page.
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
