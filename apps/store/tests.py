from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.leads.models import MoveLead
from apps.store.models import Bedrift_info
from apps.store.services import business_lead_entries


def _make_business(**overrides):
    data = dict(
        company_name="Flytt AS", email="flytt@example.com", phone="12345678",
        address="Gate 1", postal_code="0001", city="Oslo", first_name="Ola", last_name="Nordmann",
    )
    data.update(overrides)
    return Bedrift_info.objects.create(**data)


def _make_lead(business, **overrides):
    data = dict(
        flytte_type="privat", fra="A", til="B", boligtype="leilighet",
        navn="Kari Nordmann", telefon="1", epost="k@example.com", business_1=business,
    )
    data.update(overrides)
    return MoveLead.objects.create(**data)


class BedriftInfoEmailUniquenessTests(TestCase):
    def test_duplicate_email_is_rejected_at_the_db_level(self):
        """Regression test: Bedrift_info.email had no unique constraint at all, so a
        double-submitted partner-wizard POST could create two rows with the same email —
        a later signup's .filter(email=...).last() would then bind to whichever had the
        higher pk, permanently orphaning the other."""
        _make_business(email="dup@example.com")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                _make_business(email="dup@example.com")


class BusinessLeadEntriesArchivedTests(TestCase):
    def test_archived_moveleads_are_excluded_from_the_count_and_entries(self):
        """Regression test: the MoveLead query here had no archived=False filter, unlike
        every other MoveLead listing in the dashboard — a lead a staff member archived
        kept counting toward a business's usage stats and kept showing in "Mine leads"
        on the partner portal forever."""
        business = _make_business()
        active_lead = _make_lead(business, navn="Aktiv Kunde")
        archived_lead = _make_lead(business, navn="Arkivert Kunde")
        archived_lead.archived = True
        archived_lead.save(update_fields=["archived"])

        entries, movelead_count = business_lead_entries(business)
        self.assertEqual(movelead_count, 1)
        labels = [e["label"] for e in entries]
        self.assertIn(f"{active_lead.reference} — Aktiv Kunde", labels)
        self.assertNotIn(f"{archived_lead.reference} — Arkivert Kunde", labels)
