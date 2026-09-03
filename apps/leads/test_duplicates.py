import json
from datetime import timedelta
from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.leads.duplicates import (
    DUPLICATE_WINDOW,
    find_double_submit,
    find_recent_lead,
    normalize_email,
    normalize_phone,
)
from apps.leads.models import MoveLead


def _payload(**overrides):
    data = dict(
        flytte_type="privat",
        fra="Kongens gate 1, 0153 Oslo", fra_lat="59.913", fra_lon="10.752",
        til="Storgata 14, 0184 Oslo", til_lat="", til_lon="",
        boligtype="leilighet", flyttedato="2026-12-12", fleksibel="",
        beskrivelse="", navn="Ola Nordmann",
        telefon="+47 900 00 000", epost="ola@eksempel.no",
    )
    data.update(overrides)
    return data


def _make_lead(**overrides):
    fields = dict(
        flytte_type="privat", boligtype="leilighet", fleksibel=True,
        fra="Kongens gate 1, 0153 Oslo", til="Storgata 14, 0184 Oslo",
        navn="Ola Nordmann", telefon="+47 900 00 000", epost="ola@eksempel.no",
    )
    fields.update(overrides)
    return MoveLead.objects.create(**fields)


# ==========================================================================
# normalization
# ==========================================================================

class NormalizeTests(TestCase):
    def test_phone_variants_collapse(self):
        for raw in ["+47 900 00 000", "0047 90000000", "900 00 000", "90000000", "090000000"]:
            self.assertEqual(normalize_phone(raw), "90000000", raw)

    def test_phone_junk_returns_empty(self):
        for raw in ["", None, "123", "abcdef", "12"]:
            self.assertEqual(normalize_phone(raw), "", repr(raw))

    def test_email_lowercased_and_trimmed(self):
        self.assertEqual(normalize_email("  Ola@Eksempel.NO "), "ola@eksempel.no")


# ==========================================================================
# find_recent_lead
# ==========================================================================

class FindRecentLeadTests(TestCase):
    def test_matches_on_phone_even_with_different_email(self):
        _make_lead(telefon="90000000", epost="first@example.com")
        hit = find_recent_lead("+47 90 00 00 00", "totally-different@example.com")
        self.assertIsNotNone(hit)

    def test_matches_on_email_even_with_different_phone(self):
        _make_lead(telefon="90000000", epost="ola@eksempel.no")
        hit = find_recent_lead("11111111", "OLA@eksempel.no")
        self.assertIsNotNone(hit)

    def test_no_match_returns_none(self):
        _make_lead(telefon="90000000", epost="ola@eksempel.no")
        self.assertIsNone(find_recent_lead("22222222", "someone@else.no"))

    def test_lead_outside_window_is_ignored(self):
        old = _make_lead()
        MoveLead.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - DUPLICATE_WINDOW - timedelta(hours=1)
        )
        self.assertIsNone(find_recent_lead("90000000", "ola@eksempel.no"))

    def test_archived_lead_is_ignored(self):
        _make_lead(archived=True)
        self.assertIsNone(find_recent_lead("90000000", "ola@eksempel.no"))

    def test_exclude_pk(self):
        lead = _make_lead()
        self.assertIsNone(find_recent_lead("90000000", "ola@eksempel.no", exclude_pk=lead.pk))

    def test_blank_contact_never_matches(self):
        _make_lead(telefon="", epost="")
        self.assertIsNone(find_recent_lead("", ""))


class FindDoubleSubmitTests(TestCase):
    def test_identical_seconds_ago_is_a_double_submit(self):
        _make_lead()
        self.assertIsNotNone(find_double_submit("+47 900 00 000", "ola@eksempel.no"))

    def test_only_one_field_matching_is_not_a_double_submit(self):
        _make_lead(epost="ola@eksempel.no", telefon="90000000")
        self.assertIsNone(find_double_submit("11111111", "ola@eksempel.no"))

    def test_older_than_window_is_not_a_double_submit(self):
        lead = _make_lead()
        MoveLead.objects.filter(pk=lead.pk).update(created_at=timezone.now() - timedelta(minutes=5))
        self.assertIsNone(find_double_submit("90000000", "ola@eksempel.no"))


# ==========================================================================
# check endpoint
# ==========================================================================

class DuplicateCheckEndpointTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("leads:api_duplicate_check")

    def _post(self, body):
        return self.client.post(self.url, data=json.dumps(body), content_type="application/json")

    def test_reports_no_duplicate_when_none(self):
        self.assertEqual(self._post({"telefon": "90000000", "epost": "x@y.no"}).json(), {"duplicate": False})

    def test_reports_duplicate_with_reference(self):
        lead = _make_lead()
        data = self._post({"telefon": "900 00 000", "epost": "other@example.com"}).json()
        self.assertTrue(data["duplicate"])
        self.assertEqual(data["reference"], lead.reference)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_csrf_enforced(self):
        csrf_client = Client(enforce_csrf_checks=True)
        r = csrf_client.post(self.url, data=json.dumps({"telefon": "1"}), content_type="application/json")
        self.assertEqual(r.status_code, 403)

    def test_rate_limited(self):
        with mock.patch("apps.leads.api_views.DUPLICATE_CHECK_RATE", (2, 10)):
            self._post({"epost": "a@a.no"})
            self._post({"epost": "b@b.no"})
            blocked = self._post({"epost": "c@c.no"})
        self.assertEqual(blocked.status_code, 429)


# ==========================================================================
# wizard POST — the real gate
# ==========================================================================

def _active_business():
    from apps.store.models import Bedrift_info

    return Bedrift_info.objects.create(
        company_name="Oslo Flytt AS", email="oslo@example.com", phone="12345678",
        address="Gate 1", postal_code="0001", city="Oslo", first_name="O", last_name="N",
        active=True, cities="Oslo", move_type="Flyttehjelp",
    )


class WizardDuplicateGateTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_first_submission_is_normal_and_gets_assigned(self):
        business = _active_business()
        self.client.post(reverse("leads:wizard"), _payload())
        lead = MoveLead.objects.get()
        self.assertFalse(lead.is_duplicate)
        self.assertEqual(lead.business_1_id, business.pk)

    def test_repeat_without_confirmation_is_refused(self):
        _make_lead()
        response = self.client.post(reverse("leads:wizard"), _payload(epost="new@example.com"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nylig sendt inn")
        # only the original lead exists
        self.assertEqual(MoveLead.objects.count(), 1)

    def test_confirmed_repeat_is_saved_flagged_and_not_auto_assigned(self):
        original = _make_lead()
        _active_business()  # would match if auto-assign ran
        self.client.post(reverse("leads:wizard"), _payload(epost="new@example.com", bekreft_duplikat="on"))
        self.assertEqual(MoveLead.objects.count(), 2)
        dup = MoveLead.objects.exclude(pk=original.pk).get()
        self.assertTrue(dup.is_duplicate)
        self.assertEqual(dup.duplicate_of_id, original.pk)
        self.assertIsNone(dup.business_1_id)
        self.assertIsNone(dup.business_2_id)
        self.assertIsNone(dup.business_3_id)

    def test_confirmed_repeat_still_emails_the_customer(self):
        _make_lead()
        mail.outbox.clear()
        self.client.post(reverse("leads:wizard"), _payload(epost="new@example.com", bekreft_duplikat="on"))
        self.assertEqual(len(mail.outbox), 1)

    def test_accidental_double_submit_does_not_create_a_second_lead(self):
        _active_business()
        self.client.post(reverse("leads:wizard"), _payload())
        response = self.client.post(reverse("leads:wizard"), _payload())  # identical, seconds later
        self.assertRedirects(response, reverse("leads:wizard_thank_you"))
        self.assertEqual(MoveLead.objects.count(), 1)

    def test_phone_only_repeat_is_caught_server_side(self):
        _make_lead(telefon="90000000", epost="ola@eksempel.no")
        # new email, same phone, no confirmation -> refused
        response = self.client.post(
            reverse("leads:wizard"), _payload(epost="brand-new@example.com", telefon="+47 90 00 00 00")
        )
        self.assertContains(response, "nylig sendt inn", status_code=200)
        self.assertEqual(MoveLead.objects.count(), 1)


# ==========================================================================
# dashboard surfacing
# ==========================================================================

class DashboardDuplicateTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.staff = User.objects.create_user("dupstaff", password="pw", is_staff=True)
        self.client.force_login(self.staff)
        self.original = _make_lead()
        self.dup = _make_lead(navn="Ola Igjen", is_duplicate=True, duplicate_of=self.original)

    def test_lead_list_shows_pill_and_filter(self):
        r = self.client.get(reverse("dashboard:lead_list"))
        self.assertContains(r, "Duplikat")
        filtered = self.client.get(reverse("dashboard:lead_list"), {"duplicate": "1"})
        self.assertContains(filtered, "Ola Igjen")
        self.assertNotContains(filtered, ">Ola Nordmann<")

    def test_overview_shows_duplicate_card(self):
        r = self.client.get(reverse("dashboard:dashboard_overview"))
        self.assertContains(r, "må tildeles manuelt")

    def test_detail_shows_warning_and_link(self):
        r = self.client.get(reverse("dashboard:lead_detail", kwargs={"pk": self.dup.pk}))
        self.assertContains(r, "Mulig duplikat")
        self.assertContains(r, self.original.reference)

    def test_clear_duplicate_flag(self):
        r = self.client.post(reverse("dashboard:lead_clear_duplicate", kwargs={"pk": self.dup.pk}))
        self.assertRedirects(r, reverse("dashboard:lead_detail", kwargs={"pk": self.dup.pk}))
        self.dup.refresh_from_db()
        self.assertFalse(self.dup.is_duplicate)

    def test_clear_duplicate_requires_post(self):
        self.assertEqual(
            self.client.get(reverse("dashboard:lead_clear_duplicate", kwargs={"pk": self.dup.pk})).status_code,
            405,
        )
