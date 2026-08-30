# apps/store/services.py
#
# Business-lead-counting logic shared between the staff dashboard
# (apps/dashboard/views.py) and the partner-facing account portal
# (apps/userprofile/views.py) — extracted here so both sides always agree
# on "how many leads has this business received" and "how much of its
# daily/weekly/monthly cap has it used", instead of each maintaining its
# own copy that could quietly drift apart.

import re

from django.db.models import Q
from django.utils import timezone
from datetime import timedelta


def business_lead_entries(business, lead_url_resolver=None):
    """Unified, newest-first view of every lead ever routed to this business
    across both live pipelines: the direct-form flow (JobDistribution, via
    apps.core.views.send_flytteforesporsel) and the wizard flow (MoveLead's
    business_1/2/3). Neither pipeline alone tells the whole story.

    `lead_url_resolver`, if given, is called with a MoveLead and should
    return a URL for it (e.g. the dashboard's lead_detail) — the caller
    decides since the dashboard and the partner portal link to different
    places (or nowhere, if omitted).

    Returns (entries, movelead_count) — the count is returned alongside
    since callers need it separately for the "total received" figure.
    """
    from apps.leads.models import MoveLead

    entries = []
    for dist in (
        business.distribution_primary.all()
        | business.distribution_secondary.all()
        | business.distribution_tertiary.all()
    ):
        entries.append({
            "created_at": dist.created_at,
            "source": "Skjema",
            "label": str(dist.inquiry),
            "url": None,
            "status_display": None,
        })
    movelead_qs = MoveLead.objects.filter(
        Q(business_1=business) | Q(business_2=business) | Q(business_3=business),
        archived=False,
    )
    for lead in movelead_qs:
        entries.append({
            "created_at": lead.created_at,
            "source": "Veiviser",
            "label": f"{lead.reference} — {lead.navn}",
            "url": lead_url_resolver(lead) if lead_url_resolver else None,
            "status_display": lead.get_status_display(),
            "status": lead.status,
        })
    entries.sort(key=lambda entry: entry["created_at"], reverse=True)
    return entries, movelead_qs.count()


def parse_cap(raw):
    """leads_per_day/week/month are free-text CharFields — blank or
    non-numeric means "no cap", not zero."""
    try:
        value = int(raw)
        return value if value > 0 else None
    except (TypeError, ValueError):
        return None


def usage_stat(count, cap):
    percent = min(100, round(count / cap * 100)) if cap else 0
    return {"count": count, "cap": cap, "percent": percent}


def business_usage(business, lead_entries):
    """Leads received today/this week/this month across both pipelines,
    against the leads_per_day/week/month caps."""
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    def count_since(cutoff):
        return sum(1 for entry in lead_entries if entry["created_at"].date() >= cutoff)

    return {
        "today": usage_stat(count_since(today), parse_cap(business.leads_per_day)),
        "week": usage_stat(count_since(week_start), parse_cap(business.leads_per_week)),
        "month": usage_stat(count_since(month_start), parse_cap(business.leads_per_month)),
    }


# ---------------------------------------------------------------------------
# Automatic lead-to-business matching — apps.leads.views.wizard calls this
# the moment a customer submits the form (the receipt email already promises
# "we're matching you with 3 businesses", but nothing actually did that
# until now — a lead just sat as unassigned until a staff member picked it
# up by hand from the dashboard). The dashboard's own manual "Tildel til
# bedrifter" screen reuses business_matches_move for its "recommended"
# sort, so there's one heuristic, not two that could drift apart.

# MoveLead.flytte_type ("privat"/"bedrift"/"internasjonal" — what KIND of
# customer this is) and Bedrift_info.move_type ("Flyttehjelp"/"Pakking"/
# "Flyttevask"/"Lagring"/"Montering"/"Kontorflytting"/"Utlandsflytting"/
# "Dødsbo" — which SERVICES a business offers, free text from the become-a-
# partner wizard's pill buttons) are two different vocabularies that never
# literally overlap — comparing flytte_type against move_type directly (the
# original version of this heuristic, before this comment) would only ever
# match by accident, since no business's move_type field can ever contain
# the literal string "privat"/"bedrift"/"internasjonal". Bridges the two
# with the closest real service for each customer type; "privat" (by far
# the most common case) maps to "Flyttehjelp" — general moving help — since
# that's the one service every generalist mover offers.
FLYTTE_TYPE_TO_SERVICE = {
    "privat": "flyttehjelp",
    "bedrift": "kontorflytting",
    "internasjonal": "utlandsflytting",
}


def business_matches_move(business, fra, til, flytte_type):
    """True if this business's self-declared coverage (cities/move_type,
    comma-separated free text) matches a move's origin/destination and
    customer type (via FLYTTE_TYPE_TO_SERVICE). City matching is
    word-boundary based, not raw substring, since MoveLead stores full
    addresses (fra/til), not a separate city field.

    Regression note: a plain `city in destination` substring check used to
    false-positive on short Norwegian place names that are substrings of
    unrelated ones — a business covering "Ski" (a real town near Oslo)
    matched every address containing "Skien" (a different town), and "Os"
    matched every "Oslo" address. \\b...\\b requires a real word boundary on
    both sides, so "ski" no longer matches inside "skien" (no boundary
    between the shared "i" and "e"), while "oslo" itself still matches "oslo"
    exactly.
    """
    business_cities = [c.strip().lower() for c in (business.cities or "").split(",") if c.strip()]
    business_move_types = [m.strip().lower() for m in (business.move_type or "").split(",") if m.strip()]
    if not business_cities or not business_move_types:
        return False
    destination = (til or "").lower()
    origin = (fra or "").lower()
    city_match = any(
        re.search(r"\b" + re.escape(city) + r"\b", destination)
        or re.search(r"\b" + re.escape(city) + r"\b", origin)
        for city in business_cities
    )
    wanted_service = FLYTTE_TYPE_TO_SERVICE.get((flytte_type or "").lower())
    type_match = wanted_service is not None and wanted_service in business_move_types
    return city_match and type_match


def find_matching_businesses(fra, til, flytte_type, limit=3):
    """Active businesses whose coverage matches this move, up to `limit`,
    ranked by staff-set priority_score (highest first) and, among equal
    priority, by total_leads_received ascending — so automatic assignment
    spreads leads across every matching business instead of always
    piling onto the single highest-priority one."""
    from apps.store.models import Bedrift_info

    candidates = [
        business for business in Bedrift_info.objects.filter(active=True)
        if business_matches_move(business, fra, til, flytte_type)
    ]
    candidates.sort(key=lambda business: (-business.priority_score, business.total_leads_received))
    return candidates[:limit]


def record_business_assignment(business):
    """Bumps total_leads_received — the counter find_matching_businesses'
    own tiebreak ranks by, to spread leads across equally-ranked businesses.

    Regression note: nothing incremented this counter for either live
    assignment path (the wizard's automatic matching, or the dashboard's
    manual "Tildel til bedrifter"), so two businesses tied on priority_score
    ranked identically forever — the "spread fairly" tiebreak never actually
    engaged. Only the older, separate JobDistribution pipeline
    (apps.core.views.send_flytteforesporsel) ever touched this field.
    Uses F() so concurrent assignments to the same business (two leads
    landing at once) both land instead of one clobbering the other via a
    stale in-memory read."""
    from django.db.models import F

    from apps.store.models import Bedrift_info

    Bedrift_info.objects.filter(pk=business.pk).update(
        total_leads_received=F("total_leads_received") + 1
    )
    business.total_leads_received += 1


def notify_business_of_assignment(business, lead):
    """Emails a business when it's newly assigned a lead — used by both
    automatic assignment (apps.leads.views.wizard) and the dashboard's
    manual "Tildel til bedrifter" action, so a business is notified the
    same way regardless of which path assigned them. fail_silently=True:
    a broken SMTP config shouldn't block the assignment itself, only the
    notification. SMS is not implemented (no SMS provider is configured
    anywhere in this project)."""
    from django.core.mail import send_mail

    subject = f"Ny flytteforespørsel tildelt — {lead.reference}"
    message = (
        f"Hei {business.company_name},\n\n"
        "Dere har blitt tildelt en ny flytteforespørsel via Kobly.\n\n"
        f"Referanse: {lead.reference}\n"
        f"Navn: {lead.navn}\n"
        f"Telefon: {lead.telefon}\n"
        f"E-post: {lead.epost}\n"
        f"Fra: {lead.fra}\n"
        f"Til: {lead.til}\n"
        f"Type: {lead.get_flytte_type_display()}\n\n"
        "Logg inn på Kobly for mer informasjon."
    )
    send_mail(subject, message, None, [business.email], fail_silently=True)
