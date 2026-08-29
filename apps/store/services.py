# apps/store/services.py
#
# Business-lead-counting logic shared between the staff dashboard
# (apps/dashboard/views.py) and the partner-facing account portal
# (apps/userprofile/views.py) — extracted here so both sides always agree
# on "how many leads has this business received" and "how much of its
# daily/weekly/monthly cap has it used", instead of each maintaining its
# own copy that could quietly drift apart.

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
