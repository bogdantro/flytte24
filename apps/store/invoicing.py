"""Per-business lead invoicing.

An invoice lists every MoveLead routed to a business inside a date range
(the wizard pipeline — JobDistribution "Skjema" leads are not priced),
prices each at a flat per-lead rate, and subtracts any lead that has an
*approved* LeadCredit for that business. Rendered to PDF with xhtml2pdf.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.db.models import Q
from django.utils import timezone

PRICE_PER_LEAD = Decimal("350.00")  # NOK, ex. mva
VAT_RATE = Decimal("0.25")


@dataclass
class InvoiceLine:
    lead_reference: str
    lead_name: str
    created_at: object
    credited: bool

    @property
    def amount(self):
        return Decimal("0.00") if self.credited else PRICE_PER_LEAD


def period_range(period, today=None):
    """(start_date, end_date, label) for a named period ending today."""
    today = today or timezone.localdate()
    if period == "day":
        return today, today, today.strftime("%d.%m.%Y")
    if period == "week":
        start = today - timedelta(days=today.weekday())
        return start, today, f"Uke {today.isocalendar().week}, {today.year}"
    # default: month
    start = today.replace(day=1)
    return start, today, start.strftime("%B %Y")


def build_invoice(business, start, end):
    """Returns a dict with the lines + totals for `business` between `start`
    and `end`. Each bound may be a date (inclusive whole-day) or a
    timezone-aware datetime (exact instant)."""
    import datetime as _dt

    from apps.leads.models import MoveLead
    from apps.store.models import LeadCredit

    if isinstance(start, _dt.datetime):
        lo_kwargs = {"created_at__gte": start}
    else:
        lo_kwargs = {"created_at__date__gte": start}
    if isinstance(end, _dt.datetime):
        hi_kwargs = {"created_at__lte": end}
    else:
        hi_kwargs = {"created_at__date__lte": end}

    leads = MoveLead.objects.filter(
        Q(business_1=business) | Q(business_2=business) | Q(business_3=business),
        archived=False,
        **lo_kwargs,
        **hi_kwargs,
    ).order_by("created_at").distinct()

    credited_ids = set(
        LeadCredit.objects.filter(
            business=business, status="approved", lead__in=leads
        ).values_list("lead_id", flat=True)
    )

    lines = [
        InvoiceLine(
            lead_reference=lead.reference,
            lead_name=lead.navn,
            created_at=lead.created_at,
            credited=lead.pk in credited_ids,
        )
        for lead in leads
    ]
    subtotal = sum((line.amount for line in lines), Decimal("0.00"))
    vat = (subtotal * VAT_RATE).quantize(Decimal("0.01"))
    return {
        "business": business,
        "start": start,
        "end": end,
        "lines": lines,
        "lead_count": len(lines),
        "credited_count": sum(1 for line in lines if line.credited),
        "subtotal": subtotal,
        "vat": vat,
        "total": subtotal + vat,
        "price_per_lead": PRICE_PER_LEAD,
        "generated_at": timezone.now(),
    }


def render_invoice_pdf(context):
    """HTML invoice template -> PDF bytes (xhtml2pdf)."""
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa

    html = render_to_string("invoices/invoice.html", context)
    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer, encoding="utf-8")
    return buffer.getvalue()


def render_bulk_invoice_pdf(businesses, start, end):
    """One PDF, one invoice section per business, plus a grand total."""
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa

    invoices = [build_invoice(b, start, end) for b in businesses]
    grand_subtotal = sum((inv["subtotal"] for inv in invoices), Decimal("0.00"))
    grand_vat = sum((inv["vat"] for inv in invoices), Decimal("0.00"))
    html = render_to_string("invoices/bulk_invoice.html", {
        "invoices": invoices,
        "start": start,
        "end": end,
        "grand_subtotal": grand_subtotal,
        "grand_vat": grand_vat,
        "grand_total": grand_subtotal + grand_vat,
        "generated_at": timezone.now(),
    })
    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer, encoding="utf-8")
    return buffer.getvalue()
