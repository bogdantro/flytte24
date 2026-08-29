from django.contrib.auth.models import User
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


class PublicBusinessProfilePrivacyTests(TestCase):
    """Regression tests: the page's own copy claims "bare du og Kobly kan se denne
    forhåndsvisningen" (only you and Kobly can see this preview) for an inactive
    business, but the view had no auth/ownership check at all — anyone who
    guessed/enumerated a business_id could view an unapproved business's full profile."""

    def setUp(self):
        self.business = _make_business(active=False)

    def test_anonymous_visitor_gets_404_on_an_inactive_profile(self):
        response = self.client.get(f"/bedrift/{self.business.id}/")
        self.assertEqual(response.status_code, 404)

    def test_unrelated_logged_in_user_gets_404_on_an_inactive_profile(self):
        other_business = _make_business(email="other@example.com")
        other_user = User.objects.create_user("annen-bruker", password="pw")
        other_business.user = other_user
        other_business.save(update_fields=["user"])
        self.client.force_login(other_user)
        response = self.client.get(f"/bedrift/{self.business.id}/")
        self.assertEqual(response.status_code, 404)

    def test_the_businesss_own_user_can_preview_it(self):
        owner = User.objects.create_user("eier", password="pw")
        self.business.user = owner
        self.business.save(update_fields=["user"])
        self.client.force_login(owner)
        response = self.client.get(f"/bedrift/{self.business.id}/")
        self.assertEqual(response.status_code, 200)

    def test_staff_can_view_any_inactive_profile(self):
        staff = User.objects.create_user("staff-viewer", password="pw", is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(f"/bedrift/{self.business.id}/")
        self.assertEqual(response.status_code, 200)

    def test_active_business_is_publicly_visible_to_anyone(self):
        active_business = _make_business(email="active@example.com", active=True)
        response = self.client.get(f"/bedrift/{active_business.id}/")
        self.assertEqual(response.status_code, 200)
