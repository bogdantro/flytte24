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
