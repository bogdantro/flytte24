from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

RECEIPT_SUBJECT = "Vi har mottatt flytteforespørselen din"


def send_receipt_email(lead):
    """
    Sends the "we received your request" email to the customer, immediately
    after a successful wizard submit (spec §12, template id "receipt").
    """
    html = render_to_string(
        "leads/emails/receipt.html",
        {
            "lead": lead,
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
