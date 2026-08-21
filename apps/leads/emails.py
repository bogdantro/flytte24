from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.dateparse import parse_date

RECEIPT_SUBJECT = "Vi har mottatt flytteforespørselen din"

NORWEGIAN_MONTHS = [
    "januar", "februar", "mars", "april", "mai", "juni",
    "juli", "august", "september", "oktober", "november", "desember",
]


def format_norwegian_date(date):
    """Formats a date as '12. september 2026' — Django's locale-aware `date` filter
    can't be used here since LANGUAGE_CODE is 'en-us' project-wide, but every
    other string in this email (and the whole Kobly site) is Norwegian.

    Accepts a datetime.date, or an ISO "YYYY-MM-DD" string (DateField values
    aren't normalized to date objects until the model round-trips through
    the database, so callers may still be holding the raw string).
    """
    if isinstance(date, str):
        date = parse_date(date)
    return f"{date.day}. {NORWEGIAN_MONTHS[date.month - 1]} {date.year}"


def send_receipt_email(lead):
    """
    Sends the "we received your request" email to the customer, immediately
    after a successful wizard submit (spec §12, template id "receipt").
    """
    formatted_date = None
    if lead.flyttedato and not lead.fleksibel:
        formatted_date = format_norwegian_date(lead.flyttedato)

    html = render_to_string(
        "leads/emails/receipt.html",
        {
            "lead": lead,
            "formatted_date": formatted_date,
            "preheader": "Vi matcher deg med tre kvalitetssjekkede byråer. Du hører fra dem innen 24 timer.",
            "footer_note": "Du får denne e-posten fordi du sendte inn en flytteforespørsel på kobly.no.",
        },
    )
    message = EmailMultiAlternatives(
        subject=RECEIPT_SUBJECT,
        body=f"Hei {lead.navn}, vi har mottatt forespørselen din ({lead.reference}).",
        to=[lead.epost],
    )
    message.attach_alternative(html, "text/html")
    message.send()
