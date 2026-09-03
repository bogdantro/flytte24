# apps/leads/duplicates.py
#
# Repeat-submission detection for the wizard lead pipeline (MoveLead).
#
# A customer who sends a second forespørsel within DUPLICATE_WINDOW of an
# earlier one is a "repeat": the wizard warns them ("er du sikker?"), and if
# they send anyway the new lead is flagged is_duplicate=True and skipped by
# auto-assignment so a business can never be handed the same customer twice
# without a staff member deciding to.
#
# Matching is on normalized phone OR normalized email — either identifies the
# person. The normalized values are stored on MoveLead
# (telefon_normalisert / epost_normalisert, both indexed) so this is an exact
# index lookup, never a fuzzy icontains.

import re
from datetime import timedelta

from django.utils import timezone

DUPLICATE_WINDOW = timedelta(days=7)

# A brand-new lead created within this many seconds of an identical one (same
# normalized phone AND email) is treated as an accidental double-submit
# (double-click, back-button resubmit) — not a real second request.
DOUBLE_SUBMIT_SECONDS = 90


def normalize_phone(raw):
    """Norwegian mobile/landline number -> the bare 8 significant digits.

    Handles "+47 900 00 000", "0047 90000000", "90 00 00 00", "090000000"
    (stray leading zero) — all collapse to "90000000". Returns "" when there
    aren't 8 usable digits, so an unparseable number never matches another
    unparseable number.
    """
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("0047"):
        digits = digits[4:]
    elif digits.startswith("47") and len(digits) > 8:
        digits = digits[2:]
    # A single stray leading zero before an 8-digit national number.
    if len(digits) == 9 and digits.startswith("0"):
        digits = digits[1:]
    # Keep the last 8 (defensive against any remaining country-code cruft).
    if len(digits) > 8:
        digits = digits[-8:]
    return digits if len(digits) == 8 else ""


def normalize_email(raw):
    return (raw or "").strip().lower()


def find_recent_lead(telefon, epost, *, exclude_pk=None, now=None):
    """The most recent non-archived MoveLead from the same person (normalized
    phone OR normalized email) created within DUPLICATE_WINDOW, or None.

    `exclude_pk` skips a row (e.g. the lead we just created, when checking it
    against *earlier* ones).
    """
    from django.db.models import Q

    from .models import MoveLead

    phone = normalize_phone(telefon)
    email = normalize_email(epost)
    if not phone and not email:
        return None

    now = now or timezone.now()
    cutoff = now - DUPLICATE_WINDOW

    match = Q()
    if phone:
        match |= Q(telefon_normalisert=phone)
    if email:
        match |= Q(epost_normalisert=email)

    qs = MoveLead.objects.filter(match, archived=False, created_at__gte=cutoff)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.order_by("-created_at").first()


def find_double_submit(telefon, epost, *, exclude_pk=None, now=None):
    """An *identical* lead (same normalized phone AND email) created in the last
    DOUBLE_SUBMIT_SECONDS — an accidental resubmit rather than a deliberate one.
    Requires both to match (and both to be present); a repeat with only one
    field in common is a real duplicate, handled by find_recent_lead."""
    from .models import MoveLead

    phone = normalize_phone(telefon)
    email = normalize_email(epost)
    if not phone or not email:
        return None

    now = now or timezone.now()
    cutoff = now - timedelta(seconds=DOUBLE_SUBMIT_SECONDS)
    qs = MoveLead.objects.filter(
        telefon_normalisert=phone, epost_normalisert=email,
        archived=False, created_at__gte=cutoff,
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.order_by("-created_at").first()
