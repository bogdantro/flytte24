from django.contrib.auth.models import User
from django.core import mail
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.leads.models import MoveLead
from apps.store.models import Bedrift_info
from apps.store.services import (
    business_lead_entries, business_matches_move, find_matching_businesses,
    notify_business_of_assignment, record_business_assignment,
)


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

    def test_back_link_points_to_the_real_business_directory(self):
        """Regression test: this used to link back to /byraer/ — Kobly's own
        curated demo Agency catalog, not a real listing a signed-up business
        would ever appear in."""
        active_business = _make_business(email="backlink@example.com", active=True)
        response = self.client.get(f"/bedrift/{active_business.id}/")
        self.assertContains(response, 'href="/bedrifter/"')


class BusinessDirectoryTests(TestCase):
    """Regression tests: a real, approved partner business gets a public profile
    page the moment it's active, but nothing on the public site ever linked to
    it — only the business's own account page and the staff dashboard did.
    /bedrifter/ is the missing public "browse real partners" entry point
    (distinct from /byraer/, which lists Kobly's own curated demo Agency
    catalog, not real signed-up businesses)."""

    def test_only_active_businesses_are_listed(self):
        active = _make_business(email="active-dir@example.com", active=True, company_name="Aktiv Flytt")
        _make_business(email="inactive-dir@example.com", active=False, company_name="Inaktiv Flytt")
        response = self.client.get("/bedrifter/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aktiv Flytt")
        self.assertNotContains(response, "Inaktiv Flytt")

    def test_each_card_links_to_the_real_public_profile(self):
        business = _make_business(email="linked-dir@example.com", active=True, company_name="Lenket Flytt")
        response = self.client.get("/bedrifter/")
        self.assertContains(response, f'href="/bedrift/{business.id}/"')

    def test_empty_state_when_no_businesses_are_active(self):
        response = self.client.get("/bedrifter/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ingen partnere er godkjent ennå")

    def test_average_rating_reflects_real_reviews(self):
        from apps.store.models import Review

        business = _make_business(email="rated-dir@example.com", active=True, company_name="Vurdert Flytt")
        Review.objects.create(business=business, name="Kari", rating=5, comment="Toppers.")
        Review.objects.create(business=business, name="Ola", rating=3, comment="Grei.")
        response = self.client.get("/bedrifter/")
        self.assertContains(response, "4.0")
        self.assertContains(response, "(2 anmeldelser)")


class BusinessMatchesMoveTests(TestCase):
    """business_matches_move is the heuristic apps.leads.views.wizard uses to
    auto-assign a lead the instant it's submitted, and apps.dashboard.views
    _business_matches_lead reuses for its "recommended" sort — one heuristic,
    not two that could drift apart."""

    def test_matches_on_city_substring_and_mapped_service(self):
        business = _make_business(active=True, cities="Oslo, Bergen", move_type="Flyttehjelp, Pakking")
        self.assertTrue(business_matches_move(business, "Kongens gate 1, Oslo", "Storgata 2, Oslo", "privat"))

    def test_city_match_checks_both_fra_and_til(self):
        business = _make_business(active=True, cities="Bergen", move_type="Flyttehjelp")
        self.assertTrue(business_matches_move(business, "Storgata 2, Bergen", "Et sted, Trondheim", "privat"))

    def test_no_match_when_city_does_not_overlap(self):
        business = _make_business(active=True, cities="Tromsø", move_type="Flyttehjelp")
        self.assertFalse(business_matches_move(business, "Storgata 2, Oslo", "Et sted, Oslo", "privat"))

    def test_flytte_type_vocabulary_is_bridged_to_move_type_vocabulary(self):
        """Regression test: MoveLead.flytte_type ("privat"/"bedrift"/"internasjonal") and
        Bedrift_info.move_type ("Flyttehjelp"/"Kontorflytting"/"Utlandsflytting"/...) are
        two different vocabularies that never literally overlap — comparing flytte_type
        against move_type directly (the original version of this function) could only
        ever match by accident, since no business's move_type can contain the literal
        string "privat"/"bedrift"/"internasjonal"."""
        business = _make_business(active=True, cities="Oslo", move_type="Kontorflytting")
        self.assertFalse(business_matches_move(business, "A, Oslo", "B, Oslo", "privat"))
        self.assertTrue(business_matches_move(business, "A, Oslo", "B, Oslo", "bedrift"))

    def test_international_move_maps_to_utlandsflytting(self):
        business = _make_business(active=True, cities="Oslo", move_type="Utlandsflytting")
        self.assertTrue(business_matches_move(business, "A, Oslo", "B, Oslo", "internasjonal"))

    def test_no_match_with_no_coverage_set(self):
        business = _make_business(active=True)
        self.assertFalse(business_matches_move(business, "A, Oslo", "B, Oslo", "privat"))

    def test_short_city_name_does_not_false_positive_on_a_longer_unrelated_city(self):
        """Regression test: a plain `city in destination` substring check used to
        false-positive on short Norwegian place names that are substrings of
        unrelated ones — a business covering "Ski" (a real town near Oslo) matched
        every address containing "Skien" (a different town 100km away), and "Os"
        matched every "Oslo" address."""
        ski_business = _make_business(email="ski@example.com", active=True, cities="Ski", move_type="Flyttehjelp")
        self.assertFalse(business_matches_move(ski_business, "A, Bergen", "B, Skien", "privat"))
        self.assertTrue(business_matches_move(ski_business, "A, Ski", "B, Ski", "privat"))

        os_business = _make_business(email="os@example.com", active=True, cities="Os", move_type="Flyttehjelp")
        self.assertFalse(business_matches_move(os_business, "A, Bergen", "B, Oslo", "privat"))
        self.assertTrue(business_matches_move(os_business, "A, Os", "B, Os", "privat"))


class RecordBusinessAssignmentTests(TestCase):
    def test_increments_total_leads_received(self):
        """Regression test: nothing incremented this counter for either live
        assignment path (automatic or manual), so find_matching_businesses' own
        "fewest total_leads_received" tiebreak never actually engaged — two
        equally-ranked businesses ranked identically forever."""
        business = _make_business(total_leads_received=2)
        record_business_assignment(business)
        business.refresh_from_db()
        self.assertEqual(business.total_leads_received, 3)

    def test_updates_the_passed_in_instance_too(self):
        """The caller often re-ranks or re-uses the same in-memory instance
        afterward (e.g. notify_business_of_assignment) — it must see the bump
        without an explicit refresh_from_db()."""
        business = _make_business(total_leads_received=0)
        record_business_assignment(business)
        self.assertEqual(business.total_leads_received, 1)


class FindMatchingBusinessesTests(TestCase):
    def test_only_active_businesses_are_candidates(self):
        _make_business(email="a@example.com", active=False, cities="Oslo", move_type="Flyttehjelp")
        matches = find_matching_businesses("A, Oslo", "B, Oslo", "privat")
        self.assertEqual(matches, [])

    def test_ranked_by_priority_score_descending(self):
        low = _make_business(email="low@example.com", active=True, cities="Oslo", move_type="Flyttehjelp", priority_score=1)
        high = _make_business(email="high@example.com", active=True, cities="Oslo", move_type="Flyttehjelp", priority_score=9)
        matches = find_matching_businesses("A, Oslo", "B, Oslo", "privat")
        self.assertEqual(matches, [high, low])

    def test_ties_broken_by_fewest_total_leads_received(self):
        busy = _make_business(email="busy@example.com", active=True, cities="Oslo", move_type="Flyttehjelp", total_leads_received=50)
        quiet = _make_business(email="quiet@example.com", active=True, cities="Oslo", move_type="Flyttehjelp", total_leads_received=2)
        matches = find_matching_businesses("A, Oslo", "B, Oslo", "privat")
        self.assertEqual(matches, [quiet, busy])

    def test_limit_caps_the_result_at_three_by_default(self):
        for i in range(5):
            _make_business(email=f"biz{i}@example.com", active=True, cities="Oslo", move_type="Flyttehjelp")
        matches = find_matching_businesses("A, Oslo", "B, Oslo", "privat")
        self.assertEqual(len(matches), 3)


class NotifyBusinessOfAssignmentTests(TestCase):
    def test_sends_an_email_with_lead_details(self):
        business = _make_business(active=True)
        lead = _make_lead(business, navn="Kari Nordmann", telefon="90000000", fra="A, Oslo", til="B, Oslo")
        notify_business_of_assignment(business, lead)
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, [business.email])
        self.assertIn(lead.reference, sent.subject)
        self.assertIn("Kari Nordmann", sent.body)
        self.assertIn("90000000", sent.body)
