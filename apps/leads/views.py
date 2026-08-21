from django.shortcuts import render


def wizard(request):
    """Renders the 5-step lead-capture wizard (GET) — POST handling added in Task 5."""
    return render(request, "leads/wizard.html")
