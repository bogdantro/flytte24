"""Revenue math for the Økonomi dashboard.

Money in Kobly comes from the wizard lead pipeline only (``MoveLead``):
every business a lead is routed to is billed a flat ``PRICE_PER_LEAD``,
minus any ``LeadCredit`` an admin has *approved* for that (lead, business)
pair. A lead sent to three businesses is therefore three billable
"pairs". This module never touches the older ``JobDistribution`` /
``Flytteforesporsel`` pipeline, which is unpriced — same rule as
``apps.store.invoicing``.

Everything here is pure aggregation; nothing is written. The only
persisted billing state is ``store.InvoiceRun``, written when a staff
member generates an invoice PDF, and read here to tell "delivered but
not yet invoiced" leads from ones already on a sent invoice.
"""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from apps.store.invoicing import PRICE_PER_LEAD, VAT_RATE

LEAD_SLOTS = ("business_1", "business_2", "business_3")

_MONTH_LABELS_NB = [
    "januar", "februar", "mars", "april", "mai", "juni",
    "juli", "august", "september", "oktober", "november", "desember",
]


def month_label(d):
    return f"{_MONTH_LABELS_NB[d.month - 1].capitalize()} {d.year}"


def month_bounds(d):
    """(first_day, last_day) of the calendar month containing ``d``."""
    start = d.replace(day=1)
    if start.month == 12:
        nxt = start.replace(year=start.year + 1, month=1)
    else:
        nxt = start.replace(month=start.month + 1)
    return start, nxt - timedelta(days=1)


def _billable_pairs(start, end):
    """(pairs, lead_ids_by_business) for non-archived MoveLeads created in
    the inclusive date range. ``pairs`` is a dict business_id -> count of
    assignment slots; ``lead_ids_by_business`` maps business_id -> set of
    lead ids assigned to it (so credits can be matched to a real pair)."""
    from apps.leads.models import MoveLead

    leads = MoveLead.objects.filter(
        archived=False, created_at__date__gte=start, created_at__date__lte=end
    )
    pairs = defaultdict(int)
    lead_ids_by_business = defaultdict(set)
    for slot in LEAD_SLOTS:
        rows = leads.exclude(**{f"{slot}__isnull": True}).values_list(slot, "id")
        for business_id, lead_id in rows:
            pairs[business_id] += 1
            lead_ids_by_business[business_id].add(lead_id)
    return pairs, lead_ids_by_business


def _approved_credit_pairs(lead_ids_by_business):
    """business_id -> count of approved LeadCredits that land on an actual
    billable pair in the given mapping."""
    from apps.store.models import LeadCredit

    all_lead_ids = set()
    for ids in lead_ids_by_business.values():
        all_lead_ids |= ids
    credited = defaultdict(int)
    if not all_lead_ids:
        return credited
    rows = LeadCredit.objects.filter(
        status="approved", lead_id__in=all_lead_ids
    ).values_list("business_id", "lead_id")
    for business_id, lead_id in rows:
        if lead_id in lead_ids_by_business.get(business_id, ()):
            credited[business_id] += 1
    return credited


def compute(start, end):
    """Full revenue picture for the inclusive date range [start, end]."""
    from apps.store.models import Bedrift_info

    pairs, lead_ids_by_business = _billable_pairs(start, end)
    credited = _approved_credit_pairs(lead_ids_by_business)

    business_ids = set(pairs) | set(credited)
    names = dict(
        Bedrift_info.objects.filter(pk__in=business_ids).values_list("pk", "company_name")
    )
    active_ids = set(
        Bedrift_info.objects.filter(pk__in=business_ids, active=True).values_list("pk", flat=True)
    )

    by_business = []
    for business_id in business_ids:
        billable = pairs.get(business_id, 0)
        credit_count = credited.get(business_id, 0)
        net_count = billable - credit_count
        by_business.append({
            "business_id": business_id,
            "name": names.get(business_id, f"#{business_id}"),
            "active": business_id in active_ids,
            "leads": billable,
            "credited": credit_count,
            "gross": PRICE_PER_LEAD * billable,
            "credited_amount": PRICE_PER_LEAD * credit_count,
            "net": PRICE_PER_LEAD * net_count,
        })
    by_business.sort(key=lambda row: row["net"], reverse=True)

    total_pairs = sum(pairs.values())
    total_credited = sum(credited.values())
    gross = PRICE_PER_LEAD * total_pairs
    credited_amount = PRICE_PER_LEAD * total_credited
    net = gross - credited_amount
    return {
        "start": start,
        "end": end,
        "lead_pairs": total_pairs,
        "credited_pairs": total_credited,
        "gross": gross,
        "credited_amount": credited_amount,
        "net": net,
        "vat": (net * VAT_RATE).quantize(Decimal("0.01")),
        "gross_incl_vat": (net * (Decimal("1") + VAT_RATE)).quantize(Decimal("0.01")),
        "by_business": by_business,
    }


def monthly_series(months=6, today=None):
    """Net revenue per calendar month for the last ``months`` months,
    oldest first — for the trend bar chart."""
    today = today or timezone.localdate()
    series = []
    cursor = today.replace(day=1)
    starts = []
    for _ in range(months):
        starts.append(cursor)
        if cursor.month == 1:
            cursor = cursor.replace(year=cursor.year - 1, month=12)
        else:
            cursor = cursor.replace(month=cursor.month - 1)
    for start in reversed(starts):
        _s, end = month_bounds(start)
        data = compute(start, end)
        series.append({
            "label": _MONTH_LABELS_NB[start.month - 1][:3].capitalize(),
            "full_label": month_label(start),
            "net": data["net"],
            "leads": data["lead_pairs"],
        })
    return series


def projection(today=None):
    """Straight-line projection of the current month's net revenue from the
    run-rate so far. Returns None before there's a day of data."""
    today = today or timezone.localdate()
    start, end = month_bounds(today)
    so_far = compute(start, today)["net"]
    days_elapsed = (today - start).days + 1
    days_in_month = (end - start).days + 1
    if days_elapsed <= 0 or so_far <= 0:
        return None
    projected = (so_far / days_elapsed) * days_in_month
    return {
        "so_far": so_far,
        "projected": projected.quantize(Decimal("1")),
        "days_elapsed": days_elapsed,
        "days_in_month": days_in_month,
    }


def uninvoiced(today=None):
    """Per-business revenue for delivered leads that fall after the last
    period any InvoiceRun has billed that business (or all of it, if the
    business has never been invoiced). This is money earned but not yet
    on a sent invoice."""
    from django.db.models import Max

    from apps.leads.models import MoveLead
    from apps.store.models import Bedrift_info, InvoiceRun, LeadCredit

    today = today or timezone.localdate()
    # One row per business with the latest period_end any InvoiceRun billed.
    billed_through = {
        row["business_id"]: row["last"]
        for row in InvoiceRun.objects.values("business_id").annotate(last=Max("period_end"))
    }

    # Earliest lead date we might care about — a year back is plenty and
    # keeps the scan bounded. A business last invoiced more than a year ago
    # is a data-hygiene problem worth a manual look anyway.
    floor = today - timedelta(days=366)
    _pairs, lead_ids_by_business = _billable_pairs(floor, today)

    names = dict(
        Bedrift_info.objects.filter(pk__in=lead_ids_by_business.keys())
        .values_list("pk", "company_name")
    )
    rows = []
    total = Decimal("0.00")
    for business_id, lead_ids in lead_ids_by_business.items():
        cutoff = billed_through.get(business_id)
        # lead_ids is already exactly the leads assigned to this business.
        unbilled = MoveLead.objects.filter(id__in=lead_ids)
        if cutoff:
            unbilled = unbilled.filter(created_at__date__gt=cutoff)
        unbilled_ids = list(unbilled.values_list("id", flat=True))
        if not unbilled_ids:
            continue
        credited_here = LeadCredit.objects.filter(
            status="approved", business_id=business_id, lead_id__in=unbilled_ids,
        ).count()
        amount = PRICE_PER_LEAD * (len(unbilled_ids) - credited_here)
        total += amount
        rows.append({
            "business_id": business_id,
            "name": names.get(business_id, f"#{business_id}"),
            "leads": len(unbilled_ids),
            "credited": credited_here,
            "amount": amount,
            "since": cutoff,
        })
    rows.sort(key=lambda r: r["amount"], reverse=True)
    return {"rows": rows, "total": total}


def record_invoice_run(invoice, *, user=None, kind="single", batch=""):
    """Persist an InvoiceRun from a build_invoice() result dict. Called by
    the PDF endpoints so the Økonomi page knows what has been billed."""
    from apps.store.models import InvoiceRun

    def _as_date(bound):
        return bound.date() if hasattr(bound, "date") else bound

    return InvoiceRun.objects.create(
        business=invoice["business"],
        kind=kind,
        batch=batch,
        period_start=_as_date(invoice["start"]),
        period_end=_as_date(invoice["end"]),
        lead_count=invoice["lead_count"],
        credited_count=invoice["credited_count"],
        subtotal=invoice["subtotal"],
        vat=invoice["vat"],
        total=invoice["total"],
        generated_by=user if (user and user.is_authenticated) else None,
    )
