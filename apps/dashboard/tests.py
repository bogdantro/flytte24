import json

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.core.models import Article
from apps.leads.models import MoveLead
from apps.pages.models import Page, PageSection, PageSectionRevision, publish_due_pages
from apps.store.models import Bedrift_info, BusinessImage, PublicBusinessInformation, Review


def _make_lead(**overrides):
    data = dict(
        flytte_type="privat",
        fra="Kongens gate 1, 0153 Oslo",
        til="Storgata 14, 0184 Oslo",
        boligtype="leilighet",
        navn="Ola Nordmann",
        telefon="+47 900 00 000",
        epost="ola@eksempel.no",
    )
    data.update(overrides)
    return MoveLead.objects.create(**data)


class DashboardAuthTest(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user("staffuser", password="secret-pw-123", is_staff=True)
        self.regular_user = User.objects.create_user("regularuser", password="secret-pw-123", is_staff=False)

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse("dashboard:lead_list"))
        self.assertRedirects(response, f"{reverse('dashboard:login')}?next={reverse('dashboard:lead_list')}")

    def test_non_staff_user_redirected_to_login(self):
        self.client.login(username="regularuser", password="secret-pw-123")
        response = self.client.get(reverse("dashboard:lead_list"))
        self.assertRedirects(response, f"{reverse('dashboard:login')}?next={reverse('dashboard:lead_list')}")

    def test_staff_user_can_access_lead_list(self):
        self.client.login(username="staffuser", password="secret-pw-123")
        response = self.client.get(reverse("dashboard:lead_list"))
        self.assertEqual(response.status_code, 200)

    def test_login_page_renders(self):
        response = self.client.get(reverse("dashboard:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Logg inn")

    def test_login_with_valid_staff_credentials_redirects_to_overview(self):
        response = self.client.post(
            reverse("dashboard:login"),
            {"username": "staffuser", "password": "secret-pw-123"},
        )
        self.assertRedirects(response, reverse("dashboard:dashboard_overview"))

    def test_login_with_wrong_password_shows_error(self):
        response = self.client.post(
            reverse("dashboard:login"),
            {"username": "staffuser", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Feil brukernavn eller passord")

    def test_login_with_non_staff_credentials_is_denied(self):
        response = self.client.post(
            reverse("dashboard:login"),
            {"username": "regularuser", "password": "secret-pw-123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Feil brukernavn eller passord")

    def test_logout_ends_session(self):
        self.client.login(username="staffuser", password="secret-pw-123")
        self.client.post(reverse("dashboard:logout"))
        response = self.client.get(reverse("dashboard:lead_list"))
        self.assertRedirects(response, f"{reverse('dashboard:login')}?next={reverse('dashboard:lead_list')}")

    def test_logout_rejects_get(self):
        """Regression test: dashboard_logout was missing @require_POST, unlike every other
        state-changing view in this file (and unlike its own sidebar form, which already
        POSTs specifically to avoid this) — a GET request (e.g. <img src="...logg-ut/">)
        could silently log a staff member out cross-site."""
        self.client.login(username="staffuser", password="secret-pw-123")
        response = self.client.get(reverse("dashboard:logout"))
        self.assertEqual(response.status_code, 405)
        # Still logged in — the GET must not have logged them out.
        self.assertEqual(self.client.get(reverse("dashboard:lead_list")).status_code, 200)

    def test_login_redirects_to_next_after_session_expiry(self):
        """Regression test: staff_required's user_passes_test appends ?next=<original path>
        when bouncing an unauthenticated visitor to login, but dashboard_login used to always
        redirect to the overview page on success regardless — landing a staff member back on
        the overview instead of the deep link they were actually trying to reach."""
        target = reverse("dashboard:business_list")
        response = self.client.get(target)
        self.assertRedirects(response, f"{reverse('dashboard:login')}?next={target}")

        response = self.client.post(
            f"{reverse('dashboard:login')}?next={target}",
            {"username": "staffuser", "password": "secret-pw-123"},
        )
        self.assertRedirects(response, target)

    def test_login_ignores_an_unsafe_next_value(self):
        response = self.client.post(
            reverse("dashboard:login") + "?next=https://evil.example/",
            {"username": "staffuser", "password": "secret-pw-123"},
        )
        self.assertRedirects(response, reverse("dashboard:dashboard_overview"))


class DashboardLeadListTest(TestCase):
    def setUp(self):
        User.objects.create_user("staffuser", password="secret-pw-123", is_staff=True)
        self.client.login(username="staffuser", password="secret-pw-123")

    def test_lists_all_leads(self):
        _make_lead(navn="Kari Nordmann")
        _make_lead(navn="Per Hansen")
        response = self.client.get(reverse("dashboard:lead_list"))
        self.assertContains(response, "Kari Nordmann")
        self.assertContains(response, "Per Hansen")

    def test_status_filter_only_shows_matching_leads(self):
        contacted = _make_lead(navn="Kari Nordmann", status="contacted")
        _make_lead(navn="Per Hansen", status="new")
        response = self.client.get(reverse("dashboard:lead_list"), {"status": "contacted"})
        self.assertContains(response, "Kari Nordmann")
        self.assertNotContains(response, "Per Hansen")
        matching = list(response.context["leads"])
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].pk, contacted.pk)

    def test_stats_reflect_lead_counts(self):
        _make_lead(status="new")
        _make_lead(status="new")
        _make_lead(status="booked")
        response = self.client.get(reverse("dashboard:lead_list"))
        self.assertEqual(response.context["total_count"], 3)
        self.assertEqual(response.context["new_count"], 2)


class DashboardLeadDetailTest(TestCase):
    def setUp(self):
        User.objects.create_user("staffuser", password="secret-pw-123", is_staff=True)
        self.client.login(username="staffuser", password="secret-pw-123")

    def test_shows_lead_fields(self):
        lead = _make_lead(navn="Kari Nordmann", telefon="+47 911 22 333")
        response = self.client.get(reverse("dashboard:lead_detail", args=[lead.pk]))
        self.assertContains(response, "Kari Nordmann")
        self.assertContains(response, "+47 911 22 333")
        self.assertContains(response, lead.reference)

    def test_update_status_changes_lead(self):
        lead = _make_lead(status="new")
        response = self.client.post(
            reverse("dashboard:update_status", args=[lead.pk]), {"status": "contacted"}
        )
        self.assertRedirects(response, reverse("dashboard:lead_detail", args=[lead.pk]))
        lead.refresh_from_db()
        self.assertEqual(lead.status, "contacted")

    def test_update_status_rejects_unknown_value(self):
        lead = _make_lead(status="new")
        self.client.post(reverse("dashboard:update_status", args=[lead.pk]), {"status": "not-a-real-status"})
        lead.refresh_from_db()
        self.assertEqual(lead.status, "new")

    def test_archive_lead_moves_it_to_trash_instead_of_deleting(self):
        lead = _make_lead()
        response = self.client.post(reverse("dashboard:lead_archive", args=[lead.pk]))
        self.assertRedirects(response, reverse("dashboard:lead_list"))
        lead.refresh_from_db()
        self.assertTrue(lead.archived)
        self.assertIsNotNone(lead.archived_at)

    def test_archive_requires_post(self):
        lead = _make_lead()
        response = self.client.get(reverse("dashboard:lead_archive", args=[lead.pk]))
        self.assertEqual(response.status_code, 405)
        lead.refresh_from_db()
        self.assertFalse(lead.archived)

    def test_archived_lead_disappears_from_the_default_list(self):
        lead = _make_lead(navn="Kari Nordmann")
        self.client.post(reverse("dashboard:lead_archive", args=[lead.pk]))
        response = self.client.get(reverse("dashboard:lead_list"))
        self.assertNotContains(response, "Kari Nordmann")

    def test_search_matches_name_phone_email_or_reference(self):
        lead = _make_lead(navn="Kari Nordmann", telefon="+47 900 11 222", epost="kari@eksempel.no")
        _make_lead(navn="Per Hansen")
        response = self.client.get(reverse("dashboard:lead_list"), {"q": "kari@eksempel.no"})
        self.assertContains(response, "Kari Nordmann")
        self.assertNotContains(response, "Per Hansen")
        response = self.client.get(reverse("dashboard:lead_list"), {"q": lead.reference})
        self.assertContains(response, "Kari Nordmann")

    def test_date_range_filter(self):
        lead = _make_lead(navn="Kari Nordmann")
        response = self.client.get(reverse("dashboard:lead_list"), {"from": "2000-01-01", "to": "2000-01-02"})
        self.assertNotContains(response, "Kari Nordmann")
        response = self.client.get(reverse("dashboard:lead_list"), {"from": "2000-01-01"})
        self.assertContains(response, "Kari Nordmann")

    def test_follow_up_filter_shows_only_due_leads(self):
        from datetime import date, timedelta

        due = _make_lead(navn="Kari Nordmann", follow_up_at=date.today() - timedelta(days=1))
        _make_lead(navn="Per Hansen", follow_up_at=date.today() + timedelta(days=5))
        _make_lead(navn="Ola Hansen")
        response = self.client.get(reverse("dashboard:lead_list"), {"follow_up": "1"})
        self.assertContains(response, "Kari Nordmann")
        self.assertNotContains(response, "Per Hansen")
        self.assertNotContains(response, "Ola Hansen")

    def test_today_and_week_counts_exclude_archived_leads(self):
        """Regression test: lead_detail's today_counts/week_counts fed _lead_counts_by_
        business on a queryset with no archived=False — archiving a lead never actually
        lowered the today/week figure shown next to a business in the assignment list."""
        business = _make_business(active=True)
        other_lead = _make_lead(business_1=business)
        archived_lead = _make_lead(business_1=business)
        self.client.post(reverse("dashboard:lead_archive", args=[archived_lead.pk]))

        response = self.client.get(reverse("dashboard:lead_detail", args=[other_lead.pk]))
        all_shown = list(response.context["matching_businesses"]) + list(response.context["other_businesses"])
        shown = next(b for b in all_shown if b.pk == business.pk)
        self.assertEqual(shown.today_count, 1)
        self.assertEqual(shown.week_count, 1)

    def test_updating_internal_notes_and_follow_up(self):
        lead = _make_lead()
        response = self.client.post(
            reverse("dashboard:lead_update_internal", args=[lead.pk]),
            {"internal_notes": "Ring tilbake etter kl 16", "follow_up_at": "2030-01-15"},
        )
        self.assertRedirects(response, reverse("dashboard:lead_detail", args=[lead.pk]))
        lead.refresh_from_db()
        self.assertEqual(lead.internal_notes, "Ring tilbake etter kl 16")
        self.assertEqual(str(lead.follow_up_at), "2030-01-15")

    def test_clearing_follow_up_date(self):
        from datetime import date

        lead = _make_lead(follow_up_at=date(2030, 1, 1))
        self.client.post(
            reverse("dashboard:lead_update_internal", args=[lead.pk]),
            {"internal_notes": "", "follow_up_at": ""},
        )
        lead.refresh_from_db()
        self.assertIsNone(lead.follow_up_at)

    def test_status_change_and_assignment_appear_in_lead_activity_log(self):
        lead = _make_lead(status="new")
        self.client.post(reverse("dashboard:update_status", args=[lead.pk]), {"status": "contacted"})
        response = self.client.get(reverse("dashboard:lead_detail", args=[lead.pk]))
        self.assertContains(response, "Status endret til Kontaktet")


class LeadAssignBusinessesViewTests(TestCase):
    def setUp(self):
        User.objects.create_user("staffuser", password="secret-pw-123", is_staff=True)
        self.client.login(username="staffuser", password="secret-pw-123")
        self.biz1 = Bedrift_info.objects.create(
            company_name="Flytt AS", email="flytt@example.com", phone="12345678",
            address="Gate 1", postal_code="0001", city="Oslo",
            first_name="Ola", last_name="Nordmann", active=True,
        )
        self.biz2 = Bedrift_info.objects.create(
            company_name="Rask Flytting AS", email="rask@example.com", phone="87654321",
            address="Gate 2", postal_code="0002", city="Bergen",
            first_name="Kari", last_name="Nordmann", active=True,
        )

    def test_requires_post(self):
        lead = _make_lead()
        response = self.client.get(reverse("dashboard:lead_assign_businesses", args=[lead.pk]))
        self.assertEqual(response.status_code, 405)

    def test_assigns_up_to_three_businesses(self):
        lead = _make_lead()
        url = reverse("dashboard:lead_assign_businesses", args=[lead.pk])
        response = self.client.post(url, {
            "business_1": self.biz1.pk,
            "business_2": self.biz2.pk,
            "business_3": "",
        })
        self.assertRedirects(response, reverse("dashboard:lead_detail", args=[lead.pk]))
        lead.refresh_from_db()
        self.assertEqual(lead.business_1, self.biz1)
        self.assertEqual(lead.business_2, self.biz2)
        self.assertIsNone(lead.business_3)

    def test_clearing_a_selection_unassigns_it(self):
        lead = _make_lead(business_1=self.biz1)
        url = reverse("dashboard:lead_assign_businesses", args=[lead.pk])
        self.client.post(url, {"business_1": "", "business_2": "", "business_3": ""})
        lead.refresh_from_db()
        self.assertIsNone(lead.business_1)

    def test_lead_detail_shows_assigned_businesses_in_dropdowns(self):
        lead = _make_lead(business_1=self.biz1)
        response = self.client.get(reverse("dashboard:lead_detail", args=[lead.pk]))
        self.assertContains(response, "Flytt AS")
        self.assertContains(response, "Rask Flytting AS")

    def test_rejects_assigning_the_same_business_twice(self):
        lead = _make_lead()
        url = reverse("dashboard:lead_assign_businesses", args=[lead.pk])
        response = self.client.post(url, {
            "business_1": self.biz1.pk,
            "business_2": self.biz1.pk,
            "business_3": "",
        }, follow=True)
        self.assertContains(response, "kan ikke tildeles flere ganger")
        lead.refresh_from_db()
        self.assertIsNone(lead.business_1)
        self.assertIsNone(lead.business_2)


class PageListViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff2", password="pw", is_staff=True)

    def test_requires_staff_login(self):
        response = self.client.get(reverse("dashboard:page_list"))
        self.assertRedirects(response, f"{reverse('dashboard:login')}?next={reverse('dashboard:page_list')}")

    def test_empty_state_when_no_pages(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:page_list"))
        self.assertContains(response, "Ingen sider ennå")

    def test_lists_a_page_with_working_urls(self):
        page = Page.objects.create(title="Om oss", slug="om-oss", path="/om-oss/", template_key="about")
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:page_list"))
        self.assertContains(response, "Om oss")
        self.assertContains(response, reverse("dashboard:page_toggle_status", args=[page.pk]))


class PageToggleStatusViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff3", password="pw", is_staff=True)
        self.page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="draft"
        )

    def test_requires_post(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:page_toggle_status", args=[self.page.pk]))
        self.assertEqual(response.status_code, 405)

    def test_toggles_draft_to_published_and_back(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:page_toggle_status", args=[self.page.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("dashboard:page_list"))
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, "published")
        self.assertEqual(self.page.updated_by, self.staff)

        self.client.post(url)
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, "draft")


class SectionInlineUpdateViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff3b", password="pw", is_staff=True)
        self.page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="published"
        )
        self.section = PageSection.objects.create(
            page=self.page, order=1, section_type="hero", heading="Original overskrift"
        )

    def test_requires_staff_login(self):
        url = reverse("dashboard:section_inline_update", args=[self.section.pk])
        response = self.client.post(url, data="{}", content_type="application/json")
        self.assertEqual(response.status_code, 302)

    def test_requires_post(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:section_inline_update", args=[self.section.pk]))
        self.assertEqual(response.status_code, 405)

    def test_updates_an_allowed_field_and_sets_updated_by(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_inline_update", args=[self.section.pk])
        response = self.client.post(
            url,
            data=json.dumps({"field": "heading", "value": "Ny overskrift"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.section.refresh_from_db()
        self.page.refresh_from_db()
        self.assertEqual(self.section.heading, "Ny overskrift")
        self.assertEqual(self.page.updated_by, self.staff)

    def test_rejects_a_field_outside_the_whitelist(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_inline_update", args=[self.section.pk])
        response = self.client.post(
            url,
            data=json.dumps({"field": "section_type", "value": "faq"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.section.refresh_from_db()
        self.assertEqual(self.section.section_type, "hero")

    def test_rejects_a_value_longer_than_the_field_allows(self):
        """Regression test: this endpoint used to setattr()+save(update_fields=[field])
        directly, skipping full_clean() entirely — heading's max_length=300 was only
        ever enforced by contenteditable's own lack of any length limit at all, so a
        direct POST could silently store an unbounded string."""
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_inline_update", args=[self.section.pk])
        response = self.client.post(
            url,
            data=json.dumps({"field": "heading", "value": "x" * 400}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.section.refresh_from_db()
        self.assertEqual(self.section.heading, "Original overskrift")

    def test_extra_json_scalar_field_is_editable(self):
        """hero's eyebrow/HeroCard text and trust's secondary CTA live in extra_json
        rather than one of PageSection's own flat fields — field="extra_json.<key>"
        is how the live page's contenteditable spans reach them."""
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_inline_update", args=[self.section.pk])
        response = self.client.post(
            url,
            data=json.dumps({"field": "extra_json.eyebrow", "value": "Ny eyebrow"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.section.refresh_from_db()
        self.assertEqual(self.section.extra_json["eyebrow"], "Ny eyebrow")

    def test_extra_json_scalar_field_rejects_a_key_outside_the_whitelist(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_inline_update", args=[self.section.pk])
        response = self.client.post(
            url,
            data=json.dumps({"field": "extra_json.not_a_real_key", "value": "x"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_button_href_must_start_with_a_slash_or_scheme(self):
        """Regression test: button_href had no shape/scheme validation at all — a staff
        editor could type javascript:... into the edit-link popover and have it saved
        straight into a public <a href>."""
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_inline_update", args=[self.section.pk])
        response = self.client.post(
            url,
            data=json.dumps({"field": "button_href", "value": "javascript:alert(1)"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.section.refresh_from_db()
        self.assertEqual(self.section.button_href, "")

    def test_button_href_accepts_a_relative_path(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_inline_update", args=[self.section.pk])
        response = self.client.post(
            url,
            data=json.dumps({"field": "button_href", "value": "/flytteforesporsel/"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)


def _make_list_section(section_type, items, key="items"):
    page = Page.objects.create(
        title="Forside", slug=f"forside-{section_type}", path=f"/forside-{section_type}/",
        template_key="home", status="published",
    )
    return PageSection.objects.create(page=page, order=1, section_type=section_type, extra_json={key: items})


class SectionListItemUpdateViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff-li1", password="pw", is_staff=True)
        self.section = _make_list_section("faq", [
            {"question": "Opprinnelig spørsmål?", "answer": "Opprinnelig svar."},
        ])

    def test_requires_staff_login(self):
        url = reverse("dashboard:section_list_item_update", args=[self.section.pk, 0])
        response = self.client.post(url, data="{}", content_type="application/json")
        self.assertEqual(response.status_code, 302)

    def test_updates_one_items_field(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_list_item_update", args=[self.section.pk, 0])
        response = self.client.post(
            url, data=json.dumps({"question": "Nytt spørsmål?"}), content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.section.refresh_from_db()
        self.assertEqual(self.section.extra_json["items"][0]["question"], "Nytt spørsmål?")
        self.assertEqual(self.section.extra_json["items"][0]["answer"], "Opprinnelig svar.")

    def test_index_out_of_range_404s(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_list_item_update", args=[self.section.pk, 5])
        response = self.client.post(url, data=json.dumps({"question": "x"}), content_type="application/json")
        self.assertEqual(response.status_code, 404)

    def test_rejects_a_field_outside_the_section_types_spec(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_list_item_update", args=[self.section.pk, 0])
        response = self.client.post(
            url, data=json.dumps({"not_a_real_field": "x"}), content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_a_non_list_section_type_is_rejected(self):
        contact_section = PageSection.objects.create(
            page=self.section.page, order=2, section_type="hero", heading="x",
        )
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_list_item_update", args=[contact_section.pk, 0])
        response = self.client.post(url, data=json.dumps({"heading": "x"}), content_type="application/json")
        self.assertEqual(response.status_code, 400)


class SectionListItemAddViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff-li2", password="pw", is_staff=True)
        self.section = _make_list_section("services", [{"title": "Flyttehjelp", "body": "..."}])

    def test_appends_a_default_row(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_list_item_add", args=[self.section.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["index"], 1)
        self.section.refresh_from_db()
        self.assertEqual(len(self.section.extra_json["items"]), 2)

    def test_stops_at_the_max_item_cap(self):
        self.client.force_login(self.staff)
        self.section.extra_json["items"] = [{"title": "x", "body": "x"}] * 12
        self.section.save(update_fields=["extra_json"])
        url = reverse("dashboard:section_list_item_add", args=[self.section.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)


class SectionListItemDeleteViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff-li3", password="pw", is_staff=True)
        self.section = _make_list_section("cities", [
            {"name": "Oslo", "href": "/oslo/"}, {"name": "Bergen", "href": "/bergen/"},
        ])

    def test_deletes_the_item_at_index(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_list_item_delete", args=[self.section.pk, 0])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.section.refresh_from_db()
        self.assertEqual(len(self.section.extra_json["items"]), 1)
        self.assertEqual(self.section.extra_json["items"][0]["name"], "Bergen")

    def test_index_out_of_range_404s(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_list_item_delete", args=[self.section.pk, 9])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class SectionListItemImageViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff-li4", password="pw", is_staff=True)
        self.section = _make_list_section(
            "testimonials", [{"quote": "x", "name": "x", "meta": "x", "image": "old.jpg"}]
        )

    def _valid_upload(self, name="new.jpg"):
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        buffer = io.BytesIO()
        Image.new("RGB", (10, 10)).save(buffer, "JPEG")
        buffer.seek(0)
        return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")

    def test_uploads_and_sets_a_real_media_url(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_list_item_image", args=[self.section.pk, 0])
        response = self.client.post(url, {"image": self._valid_upload()})
        self.assertEqual(response.status_code, 200)
        self.section.refresh_from_db()
        from django.conf import settings
        self.assertTrue(self.section.extra_json["items"][0]["image"].startswith(settings.MEDIA_URL))

    def test_a_section_type_with_no_image_field_is_rejected(self):
        section = _make_list_section("faq", [{"question": "x", "answer": "x"}])
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_list_item_image", args=[section.pk, 0])
        response = self.client.post(url, {"image": self._valid_upload()})
        self.assertEqual(response.status_code, 400)

    def test_oversized_image_is_rejected(self):
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        buffer = io.BytesIO()
        Image.new("RGB", (1500, 1500)).save(buffer, "BMP")
        buffer.seek(0)
        oversized = SimpleUploadedFile("big.bmp", buffer.read(), content_type="image/bmp")
        self.client.force_login(self.staff)
        url = reverse("dashboard:section_list_item_image", args=[self.section.pk, 0])
        response = self.client.post(url, {"image": oversized})
        self.assertEqual(response.status_code, 400)


class PageUpdateMetaViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff3c", password="pw", is_staff=True)
        self.page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="published"
        )

    def test_requires_post(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:page_update_meta", args=[self.page.pk]))
        self.assertEqual(response.status_code, 405)

    def test_updates_meta_fields_and_sets_updated_by(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:page_update_meta", args=[self.page.pk])
        response = self.client.post(
            url,
            data=json.dumps({
                "title": "Ny tittel",
                "meta_title": "SEO-tittel",
                "meta_description": "SEO-beskrivelse.",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.page.refresh_from_db()
        self.assertEqual(self.page.title, "Ny tittel")
        self.assertEqual(self.page.meta_title, "SEO-tittel")
        self.assertEqual(self.page.meta_description, "SEO-beskrivelse.")
        self.assertEqual(self.page.updated_by, self.staff)

    def test_rejects_a_field_outside_the_whitelist(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:page_update_meta", args=[self.page.pk])
        response = self.client.post(
            url,
            data=json.dumps({"path": "/noe-annet/"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.page.refresh_from_db()
        self.assertEqual(self.page.path, "/")

    def test_rejects_a_meta_description_longer_than_the_field_allows(self):
        """Regression test: this endpoint used to setattr()+save(update_fields=[...])
        directly, skipping full_clean() entirely — meta_description's max_length=160
        was only ever enforced by the settings panel's client-side maxlength attribute,
        so a direct POST (e.g. via devtools) could silently store an unbounded string."""
        self.client.force_login(self.staff)
        url = reverse("dashboard:page_update_meta", args=[self.page.pk])
        response = self.client.post(
            url,
            data=json.dumps({"meta_description": "x" * 200}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.page.refresh_from_db()
        self.assertEqual(self.page.meta_description, "")


class PageDuplicateViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff4", password="pw", is_staff=True)
        self.page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="published"
        )
        self.section = PageSection.objects.create(
            page=self.page,
            order=1,
            section_type="hero",
            heading="Original",
            image=SimpleUploadedFile("test.gif", b"GIF87a", content_type="image/gif"),
        )

    def test_requires_post(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:page_duplicate", args=[self.page.pk]))
        self.assertEqual(response.status_code, 405)

    def test_clones_page_and_section_as_draft(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:page_duplicate", args=[self.page.pk]))
        clone = Page.objects.exclude(pk=self.page.pk).get()
        self.assertRedirects(response, reverse("dashboard:page_list"))
        self.assertEqual(clone.title, "Forside (kopi)")
        self.assertEqual(clone.status, "draft")
        self.assertNotEqual(clone.slug, self.page.slug)
        self.assertNotEqual(clone.path, self.page.path)
        self.assertEqual(clone.sections.count(), 1)
        self.assertEqual(clone.sections.first().heading, "Original")

    def test_clone_gets_its_own_image_file(self):
        self.client.force_login(self.staff)
        self.client.post(reverse("dashboard:page_duplicate", args=[self.page.pk]))
        clone_section = Page.objects.exclude(pk=self.page.pk).get().sections.first()
        self.assertNotEqual(clone_section.image.name, self.section.image.name)

    def test_duplicating_twice_gets_distinct_slugs(self):
        self.client.force_login(self.staff)
        self.client.post(reverse("dashboard:page_duplicate", args=[self.page.pk]))
        self.client.post(reverse("dashboard:page_duplicate", args=[self.page.pk]))
        self.assertEqual(Page.objects.count(), 3)
        self.assertEqual(len({p.slug for p in Page.objects.all()}), 3)

    def test_clone_of_home_page_actually_renders_at_its_own_path(self):
        """Regression test for the final-review Minor finding that a
        duplicated page's path/URL never actually resolved to anything —
        this proves the fix end to end, not just that a Page row exists."""
        self.client.force_login(self.staff)
        self.client.post(reverse("dashboard:page_duplicate", args=[self.page.pk]))
        clone = Page.objects.exclude(pk=self.page.pk).get()
        self.assertTrue(clone.path.startswith("/"))
        self.assertTrue(clone.path.endswith("/"))
        # Draft clones render for staff (still logged in from above) so they
        # can be previewed/edited before publishing.
        response = self.client.get(clone.path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Original")


class PageDeleteViewTests(TestCase):
    def setUp(self):
        # is_superuser=True: page_delete is one of the permanent-delete
        # actions restricted to superusers (see SuperuserOnlyActionsTests
        # for the regular-staff-is-forbidden case).
        self.staff = User.objects.create_user("staff5", password="pw", is_staff=True, is_superuser=True)
        self.page = Page.objects.create(
            title="Om oss", slug="om-oss", path="/om-oss/", template_key="about"
        )

    def test_requires_post(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:page_delete", args=[self.page.pk]))
        self.assertEqual(response.status_code, 405)

    def test_deletes_and_redirects(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:page_delete", args=[self.page.pk]))
        self.assertRedirects(response, reverse("dashboard:page_list"))
        self.assertFalse(Page.objects.filter(pk=self.page.pk).exists())


class BusinessListViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff6", password="pw", is_staff=True)
        self.active_biz = Bedrift_info.objects.create(
            company_name="Aktiv Flytt AS", email="aktiv@example.com", phone="12345678",
            address="Gate 1", postal_code="0001", city="Oslo",
            first_name="Ola", last_name="Nordmann", active=True,
        )
        self.inactive_biz = Bedrift_info.objects.create(
            company_name="Inaktiv Flytt AS", email="inaktiv@example.com", phone="87654321",
            address="Gate 2", postal_code="0002", city="Bergen",
            first_name="Kari", last_name="Nordmann", active=False,
        )

    def test_requires_staff_login(self):
        response = self.client.get(reverse("dashboard:business_list"))
        self.assertEqual(response.status_code, 302)

    def test_lists_all_by_default(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:business_list"))
        self.assertContains(response, "Aktiv Flytt AS")
        self.assertContains(response, "Inaktiv Flytt AS")

    def test_filters_by_active(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:business_list"), {"active": "1"})
        self.assertContains(response, "Aktiv Flytt AS")
        self.assertNotContains(response, "Inaktiv Flytt AS")

    def test_search_by_city(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:business_list"), {"q": "Bergen"})
        self.assertContains(response, "Inaktiv Flytt AS")
        self.assertNotContains(response, "Aktiv Flytt AS")

    def test_movelead_count_excludes_archived_leads(self):
        """Regression test: these Count() annotations had no archived=False filter,
        unlike every other MoveLead listing in the dashboard — archiving a lead never
        actually lowered a business's "Leads mottatt" count."""
        lead = _make_lead(business_1=self.active_biz)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:business_list"))
        business = next(b for b in response.context["businesses"] if b.pk == self.active_biz.pk)
        self.assertEqual(business.movelead_primary_count, 1)

        self.client.post(reverse("dashboard:lead_archive", args=[lead.pk]))
        response = self.client.get(reverse("dashboard:business_list"))
        business = next(b for b in response.context["businesses"] if b.pk == self.active_biz.pk)
        self.assertEqual(business.movelead_primary_count, 0)


class BusinessDetailViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff7", password="pw", is_staff=True)
        self.business = Bedrift_info.objects.create(
            company_name="Flytt AS", email="flytt@example.com", phone="12345678",
            address="Gate 1", postal_code="0001", city="Oslo",
            first_name="Ola", last_name="Nordmann", active=False,
            total_leads_received=7,
        )

    def test_requires_staff_login(self):
        url = reverse("dashboard:business_detail", args=[self.business.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_get_creates_public_info_if_missing_and_shows_totals(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:business_detail", args=[self.business.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "7")
        self.assertTrue(PublicBusinessInformation.objects.filter(business=self.business).exists())

    def test_post_updates_core_and_public_fields_but_not_active_or_total(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:business_detail", args=[self.business.pk])
        response = self.client.post(url, {
            "company_name": "Flytt AS", "company_number": "", "email": "ny@example.com",
            "phone": "12345678", "website": "", "address": "Gate 1", "postal_code": "0001",
            "city": "Oslo", "tiltaleform": "", "first_name": "Ola", "last_name": "Nordmann",
            "cities": "Oslo, Bergen", "move_type": "privat",
            "leads_per_day": "5", "leads_per_week": "", "leads_per_month": "", "priority_score": "8",
            "about_us": "Vi flytter deg trygt.", "faq": "",
        })
        self.assertRedirects(response, url)
        self.business.refresh_from_db()
        self.assertEqual(self.business.email, "ny@example.com")
        self.assertEqual(self.business.cities, "Oslo, Bergen")
        self.assertEqual(self.business.leads_per_day, "5")
        self.assertEqual(self.business.priority_score, 8)
        self.assertFalse(self.business.active)
        self.assertEqual(self.business.total_leads_received, 7)
        self.assertEqual(self.business.public_info.about_us, "Vi flytter deg trygt.")


class BusinessToggleActiveViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff8", password="pw", is_staff=True)
        self.business = Bedrift_info.objects.create(
            company_name="Flytt AS", email="flytt@example.com", phone="12345678",
            address="Gate 1", postal_code="0001", city="Oslo",
            first_name="Ola", last_name="Nordmann", active=False,
        )

    def test_requires_post(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:business_toggle_active", args=[self.business.pk]))
        self.assertEqual(response.status_code, 405)

    def test_flips_active_and_redirects_to_detail_by_default(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:business_toggle_active", args=[self.business.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("dashboard:business_detail", args=[self.business.pk]))
        self.business.refresh_from_db()
        self.assertTrue(self.business.active)

    def test_respects_next_param(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:business_toggle_active", args=[self.business.pk])
        list_url = reverse("dashboard:business_list")
        response = self.client.post(url, {"next": list_url})
        self.assertRedirects(response, list_url)

    def test_rejects_external_next_param(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:business_toggle_active", args=[self.business.pk])
        response = self.client.post(url, {"next": "https://evil.example/"})
        self.assertRedirects(response, reverse("dashboard:business_detail", args=[self.business.pk]))


class BusinessImageViewTests(TestCase):
    def setUp(self):
        # is_superuser=True: business_image_delete is restricted to
        # superusers (see SuperuserOnlyActionsTests).
        self.staff = User.objects.create_user("staff9", password="pw", is_staff=True, is_superuser=True)
        self.business = Bedrift_info.objects.create(
            company_name="Flytt AS", email="flytt@example.com", phone="12345678",
            address="Gate 1", postal_code="0001", city="Oslo",
            first_name="Ola", last_name="Nordmann",
        )
        self.public_info = PublicBusinessInformation.objects.create(business=self.business)

    def test_add_requires_post(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:business_image_add", args=[self.business.pk]))
        self.assertEqual(response.status_code, 405)

    def test_add_saves_image_and_redirects(self):
        self.client.force_login(self.staff)
        upload = SimpleUploadedFile("test.gif", b"GIF87a", content_type="image/gif")
        url = reverse("dashboard:business_image_add", args=[self.business.pk])
        response = self.client.post(url, {"image": upload})
        self.assertRedirects(response, reverse("dashboard:business_detail", args=[self.business.pk]))
        self.assertEqual(self.public_info.images.count(), 1)

    def test_add_silently_rejects_the_7th_image(self):
        self.client.force_login(self.staff)
        for i in range(6):
            BusinessImage.objects.create(
                public_info=self.public_info,
                image=SimpleUploadedFile(f"test{i}.gif", b"GIF87a", content_type="image/gif"),
            )
        upload = SimpleUploadedFile("test7.gif", b"GIF87a", content_type="image/gif")
        response = self.client.post(
            reverse("dashboard:business_image_add", args=[self.business.pk]), {"image": upload}, follow=True
        )
        self.assertEqual(self.public_info.images.count(), 6)
        self.assertContains(response, "maksimalt laste opp 6 bilder")

    def test_delete_removes_image(self):
        self.client.force_login(self.staff)
        image = BusinessImage.objects.create(
            public_info=self.public_info,
            image=SimpleUploadedFile("test.gif", b"GIF87a", content_type="image/gif"),
        )
        url = reverse("dashboard:business_image_delete", args=[self.business.pk, image.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("dashboard:business_detail", args=[self.business.pk]))
        self.assertFalse(BusinessImage.objects.filter(pk=image.pk).exists())


class ReviewViewTests(TestCase):
    def setUp(self):
        # is_superuser=True: review_delete is restricted to superusers (see
        # SuperuserOnlyActionsTests) — review_add/edit stay staff-level.
        self.staff = User.objects.create_user("staff10", password="pw", is_staff=True, is_superuser=True)
        self.business = Bedrift_info.objects.create(
            company_name="Flytt AS", email="flytt@example.com", phone="12345678",
            address="Gate 1", postal_code="0001", city="Oslo",
            first_name="Ola", last_name="Nordmann",
        )

    def test_add_requires_post(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:review_add", args=[self.business.pk]))
        self.assertEqual(response.status_code, 405)

    def test_add_creates_review(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:review_add", args=[self.business.pk])
        response = self.client.post(url, {"name": "Kari", "rating": "4", "comment": "Veldig bra!"})
        self.assertRedirects(response, reverse("dashboard:business_detail", args=[self.business.pk]))
        review = self.business.reviews.get()
        self.assertEqual(review.name, "Kari")
        self.assertEqual(review.rating, 4)

    def test_add_ignores_blank_name(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:review_add", args=[self.business.pk])
        self.client.post(url, {"name": "", "rating": "4", "comment": "Bra"})
        self.assertEqual(self.business.reviews.count(), 0)

    def test_edit_updates_fields(self):
        self.client.force_login(self.staff)
        review = Review.objects.create(business=self.business, name="Kari", rating=3, comment="Ok.")
        url = reverse("dashboard:review_edit", args=[self.business.pk, review.pk])
        self.client.post(url, {"name": "Kari Nordmann", "rating": "5", "comment": "Utmerket!"})
        review.refresh_from_db()
        self.assertEqual(review.name, "Kari Nordmann")
        self.assertEqual(review.rating, 5)

    def test_delete_removes_review(self):
        self.client.force_login(self.staff)
        review = Review.objects.create(business=self.business, name="Kari", rating=3, comment="Ok.")
        url = reverse("dashboard:review_delete", args=[self.business.pk, review.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("dashboard:business_detail", args=[self.business.pk]))
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

    def test_add_rejects_non_numeric_rating_without_crashing(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:review_add", args=[self.business.pk])
        response = self.client.post(url, {"name": "Kari", "rating": "not-a-number", "comment": "Bra"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.business.reviews.get().rating, 5)

    def test_add_rejects_out_of_range_rating(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:review_add", args=[self.business.pk])
        response = self.client.post(url, {"name": "Kari", "rating": "999", "comment": "Bra"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.business.reviews.get().rating, 5)

    def test_cannot_delete_another_businesss_review(self):
        other_business = Bedrift_info.objects.create(
            company_name="Annen AS", email="annen@example.com", phone="11111111",
            address="Gate 3", postal_code="0003", city="Trondheim",
            first_name="Per", last_name="Hansen",
        )
        review = Review.objects.create(business=other_business, name="Kari", rating=3, comment="Ok.")
        self.client.force_login(self.staff)
        url = reverse("dashboard:review_delete", args=[self.business.pk, review.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class ListPaginationTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff11", password="pw", is_staff=True)
        self.client.force_login(self.staff)
        for i in range(30):
            _make_lead(navn=f"Lead {i}")

    def test_first_page_shows_25(self):
        response = self.client.get(reverse("dashboard:lead_list"))
        self.assertEqual(len(response.context["leads"]), 25)

    def test_second_page_shows_remainder(self):
        response = self.client.get(reverse("dashboard:lead_list"), {"page": 2})
        self.assertEqual(len(response.context["leads"]), 5)

    def test_out_of_range_page_falls_back_to_last_page(self):
        response = self.client.get(reverse("dashboard:lead_list"), {"page": 999})
        self.assertEqual(response.context["leads"].number, 2)

    def test_non_numeric_page_falls_back_to_first_page(self):
        response = self.client.get(reverse("dashboard:lead_list"), {"page": "abc"})
        self.assertEqual(response.context["leads"].number, 1)

    def test_status_filter_is_preserved_in_pagination_links(self):
        response = self.client.get(reverse("dashboard:lead_list"), {"status": "new"})
        self.assertContains(response, "status=new")


class ActivityLogTests(TestCase):
    def setUp(self):
        # is_superuser=True: this class needs to actually perform permanent
        # deletes to test the log, which is now superuser-only (see
        # SuperuserOnlyActionsTests for the regular-staff case).
        self.staff = User.objects.create_user("staff12", password="pw", is_staff=True, is_superuser=True)
        self.client.force_login(self.staff)

    def test_requires_staff_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:activity_log"))
        self.assertEqual(response.status_code, 302)

    def test_permanently_deleting_an_archived_lead_creates_a_log_entry_and_lists_it(self):
        lead = _make_lead(navn="Kari Nordmann")
        reference = lead.reference
        self.client.post(reverse("dashboard:lead_archive", args=[lead.pk]))
        self.client.post(reverse("dashboard:lead_permanent_delete", args=[lead.pk]))
        response = self.client.get(reverse("dashboard:activity_log"))
        self.assertContains(response, reference)
        self.assertContains(response, "staff12")

    def test_archiving_a_lead_alone_does_not_appear_in_the_deletion_log(self):
        lead = _make_lead(navn="Kari Nordmann")
        reference = lead.reference
        self.client.post(reverse("dashboard:lead_archive", args=[lead.pk]))
        response = self.client.get(reverse("dashboard:activity_log"))
        self.assertNotContains(response, reference)

    def test_deleting_a_page_creates_a_log_entry(self):
        page = Page.objects.create(title="Om oss", slug="om-oss-log", path="/om-oss-log/", template_key="about")
        self.client.post(reverse("dashboard:page_delete", args=[page.pk]))
        response = self.client.get(reverse("dashboard:activity_log"))
        self.assertContains(response, "Om oss")

    def test_empty_state_when_nothing_deleted_yet(self):
        response = self.client.get(reverse("dashboard:activity_log"))
        self.assertContains(response, "Ingen slettinger registrert ennå")


class BusinessDetailCombinedLeadsTests(TestCase):
    """business_detail combines the JobDistribution pipeline (old direct-form
    flow, still live) with MoveLead assignments (dashboard wizard flow) —
    see apps/dashboard/views.py _business_lead_entries."""

    def setUp(self):
        self.staff = User.objects.create_user("staff13", password="pw", is_staff=True)
        self.client.force_login(self.staff)
        self.business = Bedrift_info.objects.create(
            company_name="Flytt AS", email="flytt@example.com", phone="12345678",
            address="Gate 1", postal_code="0001", city="Oslo",
            first_name="Ola", last_name="Nordmann", total_leads_received=2,
        )

    def test_total_received_combines_both_pipelines(self):
        _make_lead(business_1=self.business)
        _make_lead(business_2=self.business)
        response = self.client.get(reverse("dashboard:business_detail", args=[self.business.pk]))
        self.assertEqual(response.context["total_received"], 4)

    def test_lead_entries_lists_movelead_assignments(self):
        lead = _make_lead(navn="Kari Nordmann", business_1=self.business)
        response = self.client.get(reverse("dashboard:business_detail", args=[self.business.pk]))
        self.assertContains(response, "Kari Nordmann")
        self.assertContains(response, lead.reference)


class StatusBadgeClassTests(TestCase):
    """Business/page status badges must not reuse the lead-pipeline's
    new/contacted/booked classes (they used to, by coincidence of having a
    similar number of states) — see static/scss/dashboard.scss."""

    def setUp(self):
        self.staff = User.objects.create_user("staff14", password="pw", is_staff=True)
        self.client.force_login(self.staff)

    def test_inactive_business_does_not_reuse_lead_status_class(self):
        Bedrift_info.objects.create(
            company_name="X", email="x@example.com", phone="1", address="A",
            postal_code="0001", city="Oslo", first_name="A", last_name="B", active=False,
        )
        response = self.client.get(reverse("dashboard:business_list"))
        self.assertContains(response, "status-badge--inactive")
        self.assertNotContains(response, "status-badge--contacted")

    def test_draft_page_does_not_reuse_lead_status_class(self):
        Page.objects.create(
            title="Om oss", slug="om-oss-badge", path="/om-oss-badge/", template_key="about", status="draft"
        )
        response = self.client.get(reverse("dashboard:page_list"))
        self.assertContains(response, "status-badge--draft")
        self.assertNotContains(response, "status-badge--booked")


class LeadTrashTests(TestCase):
    def setUp(self):
        # is_superuser=True: this class exercises lead_permanent_delete's
        # own archived-lead-only guard, which is a separate concern from
        # the superuser gate covered in SuperuserOnlyActionsTests.
        self.staff = User.objects.create_user("staff15", password="pw", is_staff=True, is_superuser=True)
        self.client.force_login(self.staff)
        self.lead = _make_lead(navn="Kari Nordmann")
        self.client.post(reverse("dashboard:lead_archive", args=[self.lead.pk]))

    def test_trash_lists_archived_leads(self):
        response = self.client.get(reverse("dashboard:lead_trash"))
        self.assertContains(response, "Kari Nordmann")

    def test_restore_unarchives_and_returns_it_to_the_list(self):
        self.client.post(reverse("dashboard:lead_restore", args=[self.lead.pk]))
        self.lead.refresh_from_db()
        self.assertFalse(self.lead.archived)
        response = self.client.get(reverse("dashboard:lead_list"))
        self.assertContains(response, "Kari Nordmann")

    def test_permanent_delete_removes_it(self):
        response = self.client.post(reverse("dashboard:lead_permanent_delete", args=[self.lead.pk]))
        self.assertRedirects(response, reverse("dashboard:lead_trash"))
        self.assertEqual(MoveLead.objects.filter(pk=self.lead.pk).count(), 0)

    def test_permanent_delete_refuses_a_non_archived_lead(self):
        live_lead = _make_lead(navn="Per Hansen")
        response = self.client.post(reverse("dashboard:lead_permanent_delete", args=[live_lead.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(MoveLead.objects.filter(pk=live_lead.pk).count(), 1)

    def test_permanent_delete_also_removes_the_uploaded_image_files(self):
        """Regression test: LeadImage.lead is on_delete=CASCADE, which only ever
        deleted the LeadImage *rows* — Django never deletes the underlying file from
        storage on cascade — so a "permanent" deletion used to leave the customer's
        uploaded photos readable on disk forever."""
        import io
        from django.core.files.storage import default_storage
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.leads.models import LeadImage
        from PIL import Image

        buffer = io.BytesIO()
        Image.new("RGB", (5, 5)).save(buffer, "JPEG")
        buffer.seek(0)
        image = LeadImage.objects.create(
            lead=self.lead, image=SimpleUploadedFile("bilde.jpg", buffer.read(), content_type="image/jpeg"),
        )
        file_path = image.image.name
        self.assertTrue(default_storage.exists(file_path))

        self.client.post(reverse("dashboard:lead_permanent_delete", args=[self.lead.pk]))
        self.assertFalse(default_storage.exists(file_path))


class LeadBulkActionTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff16", password="pw", is_staff=True)
        self.client.force_login(self.staff)
        self.lead1 = _make_lead(navn="Kari Nordmann", status="new")
        self.lead2 = _make_lead(navn="Per Hansen", status="new")
        self.lead3 = _make_lead(navn="Ola Hansen", status="new")

    def test_requires_post(self):
        response = self.client.get(reverse("dashboard:lead_bulk_action"))
        self.assertEqual(response.status_code, 405)

    def test_bulk_status_change_applies_to_selected_only(self):
        self.client.post(reverse("dashboard:lead_bulk_action"), {
            "action": "contacted",
            "lead_ids": [self.lead1.pk, self.lead2.pk],
        })
        self.lead1.refresh_from_db()
        self.lead2.refresh_from_db()
        self.lead3.refresh_from_db()
        self.assertEqual(self.lead1.status, "contacted")
        self.assertEqual(self.lead2.status, "contacted")
        self.assertEqual(self.lead3.status, "new")

    def test_bulk_archive(self):
        self.client.post(reverse("dashboard:lead_bulk_action"), {
            "action": "archive",
            "lead_ids": [self.lead1.pk],
        })
        self.lead1.refresh_from_db()
        self.assertTrue(self.lead1.archived)

    def test_bulk_export_csv_returns_only_selected_rows(self):
        response = self.client.post(reverse("dashboard:lead_bulk_action"), {
            "action": "export_csv",
            "lead_ids": [self.lead1.pk],
        })
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        content = response.content.decode("utf-8-sig")  # a leading BOM is now written for Excel's sake
        self.assertIn("Kari Nordmann", content)
        self.assertNotIn("Per Hansen", content)

    def test_no_selection_shows_error(self):
        response = self.client.post(
            reverse("dashboard:lead_bulk_action"), {"action": "archive"}, follow=True
        )
        self.assertContains(response, "Ingen forespørsler valgt")

    def test_redirects_back_with_preserved_querystring(self):
        response = self.client.post(reverse("dashboard:lead_bulk_action"), {
            "action": "archive",
            "lead_ids": [self.lead1.pk],
            "redirect_qs": "status=new",
        })
        self.assertRedirects(response, reverse("dashboard:lead_list") + "?status=new")


class LeadExportCsvTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff17", password="pw", is_staff=True)
        self.client.force_login(self.staff)

    def test_export_matches_current_filter(self):
        _make_lead(navn="Kari Nordmann", status="new")
        _make_lead(navn="Per Hansen", status="booked")
        response = self.client.get(reverse("dashboard:lead_export_csv"), {"status": "new"})
        content = response.content.decode("utf-8")
        self.assertIn("Kari Nordmann", content)
        self.assertNotIn("Per Hansen", content)

    def test_archived_leads_are_excluded(self):
        lead = _make_lead(navn="Kari Nordmann")
        self.client.post(reverse("dashboard:lead_archive", args=[lead.pk]))
        response = self.client.get(reverse("dashboard:lead_export_csv"))
        self.assertNotIn("Kari Nordmann", response.content.decode("utf-8"))


class LeadAssignmentSuggestionTests(TestCase):
    """The 'Tildel til bedrifter' dropdown groups businesses whose
    cities/move_type overlap the lead's fra/til/flytte_type as 'recommended'
    — see apps/dashboard/views.py _business_matches_lead."""

    def setUp(self):
        self.staff = User.objects.create_user("staff18", password="pw", is_staff=True)
        self.client.force_login(self.staff)

    def test_matching_business_is_recommended(self):
        Bedrift_info.objects.create(
            company_name="Oslo Flytt AS", email="oslo@example.com", phone="1",
            address="A", postal_code="0001", city="Oslo", first_name="A", last_name="B",
            active=True, cities="Oslo", move_type="Flyttehjelp",
        )
        lead = _make_lead(flytte_type="privat", til="Storgata 14, 0184 Oslo")
        response = self.client.get(reverse("dashboard:lead_detail", args=[lead.pk]))
        self.assertIn("Oslo Flytt AS", [b.company_name for b in response.context["matching_businesses"]])

    def test_non_matching_business_is_not_recommended(self):
        Bedrift_info.objects.create(
            company_name="Bergen Flytt AS", email="bergen@example.com", phone="1",
            address="A", postal_code="0001", city="Bergen", first_name="A", last_name="B",
            active=True, cities="Bergen", move_type="Kontorflytting",
        )
        lead = _make_lead(flytte_type="privat", til="Storgata 14, 0184 Oslo")
        response = self.client.get(reverse("dashboard:lead_detail", args=[lead.pk]))
        self.assertIn("Bergen Flytt AS", [b.company_name for b in response.context["other_businesses"]])
        self.assertNotIn("Bergen Flytt AS", [b.company_name for b in response.context["matching_businesses"]])


def _make_business(**overrides):
    data = dict(
        company_name="Flytt AS", email="flytt@example.com", phone="12345678",
        address="Gate 1", postal_code="0001", city="Oslo",
        first_name="Ola", last_name="Nordmann",
    )
    data.update(overrides)
    return Bedrift_info.objects.create(**data)


class BusinessPhoneValidationTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff19", password="pw", is_staff=True)
        self.client.force_login(self.staff)
        self.business = _make_business()

    def _post(self, phone):
        return self.client.post(reverse("dashboard:business_detail", args=[self.business.pk]), {
            "company_name": "Flytt AS", "company_number": "", "email": "flytt@example.com",
            "phone": phone, "website": "", "address": "Gate 1", "postal_code": "0001",
            "city": "Oslo", "tiltaleform": "", "first_name": "Ola", "last_name": "Nordmann",
            "cities": "", "move_type": "", "leads_per_day": "", "leads_per_week": "",
            "leads_per_month": "", "priority_score": "0", "tags": "", "internal_notes": "",
            "about_us": "", "faq": "",
        })

    def test_rejects_letters_in_phone(self):
        response = self._post("call me maybe")
        self.assertEqual(response.status_code, 200)  # re-renders the form with errors, no redirect
        self.business.refresh_from_db()
        self.assertEqual(self.business.phone, "12345678")

    def test_accepts_a_formatted_phone_number(self):
        response = self._post("+47 900 00 000")
        self.assertRedirects(response, reverse("dashboard:business_detail", args=[self.business.pk]))
        self.business.refresh_from_db()
        self.assertEqual(self.business.phone, "+47 900 00 000")


class BusinessTagsAndNotesTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff20", password="pw", is_staff=True)
        self.client.force_login(self.staff)
        self.business = _make_business(tags="VIP, treg respons")

    def test_tags_shown_in_business_list(self):
        response = self.client.get(reverse("dashboard:business_list"))
        self.assertContains(response, "VIP, treg respons")

    def test_internal_notes_not_shown_on_public_profile(self):
        self.business.internal_notes = "Ikke stol på denne bedriften."
        self.business.save(update_fields=["internal_notes"])
        response = self.client.get(reverse("public_business_profile", args=[self.business.pk]))
        self.assertNotContains(response, "Ikke stol på denne bedriften.")


class BusinessUsageBarTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff21", password="pw", is_staff=True)
        self.client.force_login(self.staff)

    def test_usage_reflects_todays_movelead_assignments_against_cap(self):
        business = _make_business(leads_per_day="2")
        _make_lead(business_1=business)
        response = self.client.get(reverse("dashboard:business_detail", args=[business.pk]))
        self.assertEqual(response.context["usage"]["today"]["count"], 1)
        self.assertEqual(response.context["usage"]["today"]["cap"], 2)
        self.assertEqual(response.context["usage"]["today"]["percent"], 50)

    def test_blank_cap_means_no_limit(self):
        business = _make_business()
        response = self.client.get(reverse("dashboard:business_detail", args=[business.pk]))
        self.assertIsNone(response.context["usage"]["today"]["cap"])


class BusinessImportTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff22", password="pw", is_staff=True)
        self.client.force_login(self.staff)
        self.header = (
            "company_name,company_number,email,phone,website,address,postal_code,city,"
            "tiltaleform,first_name,last_name,cities,move_type,leads_per_day,leads_per_week,leads_per_month"
        )

    def test_requires_staff_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:business_import"))
        self.assertEqual(response.status_code, 302)

    def test_imports_valid_rows(self):
        csv_content = self.header + "\nNy Flytt AS,,ny@example.com,12345678,,Gate 1,0001,Oslo,,Ola,Nordmann,Oslo,privat,,,"
        upload = SimpleUploadedFile("businesses.csv", csv_content.encode("utf-8"), content_type="text/csv")
        response = self.client.post(reverse("dashboard:business_import"), {"csv_file": upload}, follow=True)
        self.assertTrue(Bedrift_info.objects.filter(company_name="Ny Flytt AS").exists())
        imported = Bedrift_info.objects.get(company_name="Ny Flytt AS")
        self.assertFalse(imported.active)
        self.assertContains(response, "1 bedrifter importert")

    def test_skips_and_reports_invalid_rows(self):
        csv_content = self.header + "\n,,not-an-email,bad-phone!!!,,,,,,,,,,,,"
        upload = SimpleUploadedFile("businesses.csv", csv_content.encode("utf-8"), content_type="text/csv")
        response = self.client.post(reverse("dashboard:business_import"), {"csv_file": upload}, follow=True)
        self.assertEqual(Bedrift_info.objects.count(), 0)
        self.assertContains(response, "rader ble hoppet over")

    def test_no_file_shows_error(self):
        response = self.client.post(reverse("dashboard:business_import"), {}, follow=True)
        self.assertContains(response, "Ingen fil valgt")


class LeadAssignmentNotificationTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff23", password="pw", is_staff=True)
        self.client.force_login(self.staff)
        self.biz1 = _make_business(company_name="Flytt AS", email="flytt@example.com", active=True)
        self.biz2 = _make_business(company_name="Rask Flytting AS", email="rask@example.com", active=True)

    def test_newly_assigned_business_gets_an_email(self):
        lead = _make_lead()
        self.client.post(reverse("dashboard:lead_assign_businesses", args=[lead.pk]), {
            "business_1": self.biz1.pk, "business_2": "", "business_3": "",
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["flytt@example.com"])
        self.assertIn(lead.reference, mail.outbox[0].body)

    def test_reassigning_the_same_business_does_not_resend(self):
        lead = _make_lead(business_1=self.biz1)
        mail.outbox.clear()
        self.client.post(reverse("dashboard:lead_assign_businesses", args=[lead.pk]), {
            "business_1": self.biz1.pk, "business_2": "", "business_3": "",
        })
        self.assertEqual(len(mail.outbox), 0)

    def test_swapping_to_a_different_business_only_notifies_the_new_one(self):
        lead = _make_lead(business_1=self.biz1)
        mail.outbox.clear()
        self.client.post(reverse("dashboard:lead_assign_businesses", args=[lead.pk]), {
            "business_1": self.biz2.pk, "business_2": "", "business_3": "",
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["rask@example.com"])

    def test_newly_assigned_business_gets_total_leads_received_incremented(self):
        """Regression test: nothing incremented this counter for either live
        assignment path, so find_matching_businesses' own "spread fairly"
        tiebreak never actually engaged. Manual dashboard assignment must bump
        it exactly like the wizard's automatic assignment does."""
        lead = _make_lead()
        self.client.post(reverse("dashboard:lead_assign_businesses", args=[lead.pk]), {
            "business_1": self.biz1.pk, "business_2": "", "business_3": "",
        })
        self.biz1.refresh_from_db()
        self.assertEqual(self.biz1.total_leads_received, 1)

    def test_reassigning_the_same_business_does_not_double_increment(self):
        lead = _make_lead(business_1=self.biz1)
        self.biz1.refresh_from_db()
        before = self.biz1.total_leads_received
        self.client.post(reverse("dashboard:lead_assign_businesses", args=[lead.pk]), {
            "business_1": self.biz1.pk, "business_2": "", "business_3": "",
        })
        self.biz1.refresh_from_db()
        self.assertEqual(self.biz1.total_leads_received, before)

    def test_a_notification_failure_does_not_500_or_lose_the_assignment(self):
        """Regression test: notify_business_of_assignment used to be called with
        no try/except in this view (unlike the wizard's automatic path, which
        always wrapped it) — a bad/blank business email could turn an
        already-saved assignment into an unhandled 500 with no confirmation it
        actually happened."""
        from unittest.mock import patch

        lead = _make_lead()
        with patch("apps.dashboard.views.notify_business_of_assignment", side_effect=ValueError("bad address")):
            response = self.client.post(reverse("dashboard:lead_assign_businesses", args=[lead.pk]), {
                "business_1": self.biz1.pk, "business_2": "", "business_3": "",
            })
        self.assertEqual(response.status_code, 302)
        lead.refresh_from_db()
        self.assertEqual(lead.business_1_id, self.biz1.pk)


class SectionRevisionHistoryTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff24", password="pw", is_staff=True)
        self.client.force_login(self.staff)
        self.page = Page.objects.create(
            title="Forside", slug="forside-hist", path="/forside-hist/", template_key="home", status="published"
        )
        self.section = PageSection.objects.create(
            page=self.page, order=1, section_type="hero", heading="Original overskrift"
        )

    def _update(self, value):
        return self.client.post(
            reverse("dashboard:section_inline_update", args=[self.section.pk]),
            data=json.dumps({"field": "heading", "value": value}),
            content_type="application/json",
        )

    def test_editing_a_field_records_the_previous_value(self):
        self._update("Ny overskrift")
        revision = PageSectionRevision.objects.get(section=self.section)
        self.assertEqual(revision.field, "heading")
        self.assertEqual(revision.previous_value, "Original overskrift")
        self.assertEqual(revision.changed_by, self.staff)

    def test_saving_the_same_value_does_not_create_a_revision(self):
        self._update("Original overskrift")
        self.assertEqual(PageSectionRevision.objects.count(), 0)

    def test_page_history_requires_staff_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:page_history", args=[self.page.pk]))
        self.assertEqual(response.status_code, 302)

    def test_page_history_lists_revisions(self):
        self._update("Ny overskrift")
        response = self.client.get(reverse("dashboard:page_history", args=[self.page.pk]))
        self.assertContains(response, "Original overskrift")

    def test_restoring_a_revision_reverts_the_field_and_is_itself_reversible(self):
        self._update("Ny overskrift")
        revision = PageSectionRevision.objects.get(section=self.section)
        response = self.client.post(reverse("dashboard:section_revision_restore", args=[revision.pk]))
        self.assertRedirects(response, reverse("dashboard:page_history", args=[self.page.pk]))
        self.section.refresh_from_db()
        self.assertEqual(self.section.heading, "Original overskrift")
        # restoring created a second revision capturing "Ny overskrift", so the restore is itself undoable
        self.assertEqual(PageSectionRevision.objects.filter(section=self.section).count(), 2)


class PageSchedulePublishTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff25", password="pw", is_staff=True)
        self.client.force_login(self.staff)
        self.page = Page.objects.create(
            title="Om oss", slug="om-oss-sched", path="/om-oss-sched/", template_key="about", status="draft"
        )

    def test_requires_post(self):
        response = self.client.get(reverse("dashboard:page_schedule_publish", args=[self.page.pk]))
        self.assertEqual(response.status_code, 405)

    def test_scheduling_a_future_time_keeps_page_as_draft(self):
        self.client.post(
            reverse("dashboard:page_schedule_publish", args=[self.page.pk]), {"publish_at": "2099-01-01T10:00"}
        )
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, "draft")
        self.assertIsNotNone(self.page.publish_at)

    def test_scheduling_a_past_time_publishes_immediately(self):
        self.client.post(
            reverse("dashboard:page_schedule_publish", args=[self.page.pk]), {"publish_at": "2000-01-01T10:00"}
        )
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, "published")
        self.assertIsNone(self.page.publish_at)

    def test_clearing_cancels_the_schedule_without_changing_status(self):
        self.page.publish_at = "2099-01-01T10:00:00Z"
        self.page.save(update_fields=["publish_at"])
        self.client.post(reverse("dashboard:page_schedule_publish", args=[self.page.pk]), {"publish_at": ""})
        self.page.refresh_from_db()
        self.assertIsNone(self.page.publish_at)
        self.assertEqual(self.page.status, "draft")

    def test_publish_due_pages_flips_status_once_due(self):
        self.page.publish_at = "2000-01-01T10:00:00Z"
        self.page.save(update_fields=["publish_at"])
        publish_due_pages()
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, "published")

    def test_page_list_triggers_publish_due_pages(self):
        self.page.publish_at = "2000-01-01T10:00:00Z"
        self.page.save(update_fields=["publish_at"])
        self.client.get(reverse("dashboard:page_list"))
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, "published")


class DraftPreviewBannerTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff26", password="pw", is_staff=True)

    def test_staff_sees_draft_tag_on_an_unpublished_page(self):
        page = Page.objects.create(
            title="Forside", slug="forside-draft", path="/", template_key="home", status="draft"
        )
        self.client.force_login(self.staff)
        response = self.client.get("/")
        self.assertContains(response, "UTKAST")

    def test_no_draft_tag_on_a_published_page(self):
        page = Page.objects.create(
            title="Forside", slug="forside-pub", path="/", template_key="home", status="published"
        )
        self.client.force_login(self.staff)
        response = self.client.get("/")
        self.assertNotContains(response, "UTKAST")

    def test_anonymous_visitor_does_not_get_the_draft_home_page(self):
        Page.objects.create(
            title="Forside", slug="forside-draft2", path="/", template_key="home", status="draft",
            meta_title="Draft-only-title",
        )
        response = self.client.get("/")
        self.assertNotContains(response, "Draft-only-title")

    def test_staff_previewing_draft_home_gets_the_actual_draft_page_in_context(self):
        page = Page.objects.create(
            title="Forside", slug="forside-draft3", path="/", template_key="home", status="draft"
        )
        self.client.force_login(self.staff)
        response = self.client.get("/")
        self.assertEqual(response.context["page"], page)


class DashboardOverviewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff27", password="pw", is_staff=True)
        self.client.force_login(self.staff)

    def test_requires_staff_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:dashboard_overview"))
        self.assertEqual(response.status_code, 302)

    def test_root_url_is_the_overview_not_the_lead_list(self):
        response = self.client.get("/dashboard/")
        self.assertEqual(response.resolver_match.func.__name__, "dashboard_overview")

    def test_stats_reflect_active_leads_only(self):
        from datetime import date, timedelta

        _make_lead(navn="New today", status="new")
        _make_lead(navn="Follow up due", follow_up_at=date.today() - timedelta(days=1))
        archived = _make_lead(navn="Archived")
        self.client.post(reverse("dashboard:lead_archive", args=[archived.pk]))

        response = self.client.get(reverse("dashboard:dashboard_overview"))
        self.assertEqual(response.context["new_today"], 2)
        self.assertEqual(response.context["follow_up_due"], 1)

    def test_businesses_near_cap_are_surfaced(self):
        business = _make_business(leads_per_day="1", active=True)
        _make_lead(business_1=business)
        response = self.client.get(reverse("dashboard:dashboard_overview"))
        names = [entry["business"].company_name for entry in response.context["businesses_near_cap"]]
        self.assertIn(business.company_name, names)

    def test_an_archived_lead_no_longer_counts_toward_near_cap(self):
        """Regression test: _businesses_near_cap fed on a plain MoveLead.objects.filter(...)
        with no archived=False, unlike every other MoveLead listing in the dashboard —
        archiving a lead that had put a business near its cap never actually cleared it
        from this list."""
        business = _make_business(leads_per_day="1", active=True)
        lead = _make_lead(business_1=business)
        self.client.post(reverse("dashboard:lead_archive", args=[lead.pk]))
        response = self.client.get(reverse("dashboard:dashboard_overview"))
        names = [entry["business"].company_name for entry in response.context["businesses_near_cap"]]
        self.assertNotIn(business.company_name, names)

    def test_recent_leads_shown(self):
        _make_lead(navn="Kari Nordmann")
        response = self.client.get(reverse("dashboard:dashboard_overview"))
        self.assertContains(response, "Kari Nordmann")


class GlobalSearchTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff28", password="pw", is_staff=True)
        self.client.force_login(self.staff)

    def test_requires_staff_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:global_search"))
        self.assertEqual(response.status_code, 302)

    def test_empty_query_shows_no_results_sections(self):
        response = self.client.get(reverse("dashboard:global_search"))
        self.assertEqual(list(response.context["leads"]), [])

    def test_finds_a_lead_a_business_and_a_page(self):
        lead = _make_lead(navn="Unikt Søkeord Nordmann")
        business = _make_business(company_name="Unikt Søkeord AS")
        page = Page.objects.create(
            title="Unikt Søkeord Side", slug="unikt-sokeord-side", path="/unikt-sokeord-side/", template_key="about"
        )
        response = self.client.get(reverse("dashboard:global_search"), {"q": "Unikt Søkeord"})
        self.assertContains(response, lead.navn)
        self.assertContains(response, business.company_name)
        self.assertContains(response, page.title)

    def test_search_includes_archived_leads(self):
        lead = _make_lead(navn="Arkivert Søketreff")
        self.client.post(reverse("dashboard:lead_archive", args=[lead.pk]))
        response = self.client.get(reverse("dashboard:global_search"), {"q": "Arkivert Søketreff"})
        self.assertContains(response, "Arkivert Søketreff")


class SuperuserOnlyActionsTests(TestCase):
    """Permanent-delete actions are restricted to superusers (see
    apps/dashboard/views.py superuser_required) — regular is_staff users can
    archive/edit/toggle but not permanently remove anything."""

    def setUp(self):
        self.staff = User.objects.create_user("staff29", password="pw", is_staff=True, is_superuser=False)
        self.admin = User.objects.create_user("admin29", password="pw", is_staff=True, is_superuser=True)
        self.business = _make_business()

    def test_staff_cannot_permanently_delete_an_archived_lead(self):
        self.client.force_login(self.staff)
        lead = _make_lead()
        self.client.post(reverse("dashboard:lead_archive", args=[lead.pk]))
        response = self.client.post(reverse("dashboard:lead_permanent_delete", args=[lead.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(MoveLead.objects.filter(pk=lead.pk).count(), 1)

    def test_superuser_can_permanently_delete_an_archived_lead(self):
        self.client.force_login(self.admin)
        lead = _make_lead()
        self.client.post(reverse("dashboard:lead_archive", args=[lead.pk]))
        response = self.client.post(reverse("dashboard:lead_permanent_delete", args=[lead.pk]))
        self.assertRedirects(response, reverse("dashboard:lead_trash"))
        self.assertEqual(MoveLead.objects.filter(pk=lead.pk).count(), 0)

    def test_staff_cannot_delete_a_page(self):
        self.client.force_login(self.staff)
        page = Page.objects.create(title="Om oss", slug="om-oss-perm", path="/om-oss-perm/", template_key="about")
        response = self.client.post(reverse("dashboard:page_delete", args=[page.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Page.objects.filter(pk=page.pk).exists())

    def test_staff_cannot_delete_a_business_review(self):
        self.client.force_login(self.staff)
        review = Review.objects.create(business=self.business, name="Kari", rating=3, comment="Ok.")
        response = self.client.post(reverse("dashboard:review_delete", args=[self.business.pk, review.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Review.objects.filter(pk=review.pk).exists())

    def test_staff_cannot_delete_a_business_image(self):
        self.client.force_login(self.staff)
        public_info = PublicBusinessInformation.objects.create(business=self.business)
        image = BusinessImage.objects.create(
            public_info=public_info,
            image=SimpleUploadedFile("test.gif", b"GIF87a", content_type="image/gif"),
        )
        response = self.client.post(
            reverse("dashboard:business_image_delete", args=[self.business.pk, image.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(BusinessImage.objects.filter(pk=image.pk).exists())

    def test_anonymous_user_is_redirected_not_403d(self):
        page = Page.objects.create(title="Om oss", slug="om-oss-anon", path="/om-oss-anon/", template_key="about")
        response = self.client.post(reverse("dashboard:page_delete", args=[page.pk]))
        self.assertEqual(response.status_code, 302)

    def test_delete_buttons_hidden_from_non_superuser_staff(self):
        self.client.force_login(self.staff)
        lead = _make_lead()
        self.client.post(reverse("dashboard:lead_archive", args=[lead.pk]))
        response = self.client.get(reverse("dashboard:lead_trash"))
        self.assertNotContains(response, "Slett permanent")

    def test_delete_buttons_shown_to_superuser(self):
        self.client.force_login(self.admin)
        lead = _make_lead()
        self.client.post(reverse("dashboard:lead_archive", args=[lead.pk]))
        response = self.client.get(reverse("dashboard:lead_trash"))
        self.assertContains(response, "Slett permanent")


class LoginRateLimitTests(TestCase):
    def setUp(self):
        User.objects.create_user("staffuser2", password="secret-pw-123", is_staff=True)
        cache.clear()

    def test_locks_out_after_five_failed_attempts(self):
        for _ in range(5):
            self.client.post(
                reverse("dashboard:login"), {"username": "staffuser2", "password": "wrong"}
            )
        response = self.client.post(
            reverse("dashboard:login"), {"username": "staffuser2", "password": "secret-pw-123"}
        )
        self.assertContains(response, "For mange mislykkede innloggingsforsøk")

    def test_successful_login_clears_the_counter(self):
        self.client.post(reverse("dashboard:login"), {"username": "staffuser2", "password": "wrong"})
        response = self.client.post(
            reverse("dashboard:login"), {"username": "staffuser2", "password": "secret-pw-123"}
        )
        self.assertRedirects(response, reverse("dashboard:dashboard_overview"))

    def test_lockout_is_scoped_per_username_not_global(self):
        User.objects.create_user("otherstaff", password="other-pw-123", is_staff=True)
        for _ in range(5):
            self.client.post(reverse("dashboard:login"), {"username": "staffuser2", "password": "wrong"})
        response = self.client.post(
            reverse("dashboard:login"), {"username": "otherstaff", "password": "other-pw-123"}
        )
        self.assertRedirects(response, reverse("dashboard:dashboard_overview"))


class ArticleAdminTests(TestCase):
    """Blog articles previously had no dashboard screen at all — only editable via the
    seed_marketing_content management command."""

    def setUp(self):
        self.staff = User.objects.create_user("staff-blog", password="pw", is_staff=True)
        self.superuser = User.objects.create_user("superuser-blog", password="pw", is_staff=True, is_superuser=True)
        self.article = Article.objects.create(
            slug="test-artikkel", title="Test Artikkel", ingress="En kort ingress.",
            date="2026-01-01", read_minutes=5,
            blocks=[{"type": "h2", "text": "Overskrift"}, {"type": "p", "text": "Brødtekst."}],
        )

    def test_list_requires_staff_login(self):
        response = self.client.get(reverse("dashboard:article_list"))
        self.assertEqual(response.status_code, 302)

    def test_list_shows_existing_articles(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:article_list"))
        self.assertContains(response, "Test Artikkel")

    def test_add_form_renders(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:article_add"))
        self.assertEqual(response.status_code, 200)

    def test_valid_post_creates_an_article(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:article_add"), {
            "title": "Ny Artikkel", "slug": "ny-artikkel", "ingress": "Ingress her.",
            "header_image": "", "date": "2026-02-01", "read_minutes": "3",
            "blocks_json": json.dumps([{"type": "p", "text": "Hei."}]),
        })
        article = Article.objects.get(slug="ny-artikkel")
        self.assertRedirects(response, reverse("dashboard:article_edit", args=[article.pk]))
        self.assertEqual(article.title, "Ny Artikkel")
        self.assertEqual(article.blocks, [{"type": "p", "text": "Hei."}])

    def test_invalid_json_in_blocks_is_rejected(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:article_add"), {
            "title": "Ny Artikkel", "slug": "ny-artikkel-2", "ingress": "Ingress her.",
            "header_image": "", "date": "2026-02-01", "read_minutes": "3",
            "blocks_json": "not valid json{{{",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Article.objects.filter(slug="ny-artikkel-2").exists())

    def test_blocks_json_must_be_a_list(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:article_add"), {
            "title": "Ny Artikkel", "slug": "ny-artikkel-3", "ingress": "Ingress her.",
            "header_image": "", "date": "2026-02-01", "read_minutes": "3",
            "blocks_json": json.dumps({"type": "p", "text": "Hei."}),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Article.objects.filter(slug="ny-artikkel-3").exists())

    def test_unknown_block_type_is_rejected(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:article_add"), {
            "title": "Ny Artikkel", "slug": "ny-artikkel-4", "ingress": "Ingress her.",
            "header_image": "", "date": "2026-02-01", "read_minutes": "3",
            "blocks_json": json.dumps([{"type": "not-a-real-type", "text": "Hei."}]),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Article.objects.filter(slug="ny-artikkel-4").exists())

    def test_list_block_with_non_string_items_is_rejected(self):
        """Regression test: only "type" was validated, so {"type": "list",
        "items": "not a list"} passed straight through — since a string is
        itself iterable, home.html's {% for item in block.items %} would
        then render each individual character as its own <li>."""
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:article_add"), {
            "title": "Ny Artikkel", "slug": "ny-artikkel-5", "ingress": "Ingress her.",
            "header_image": "", "date": "2026-02-01", "read_minutes": "3",
            "blocks_json": json.dumps([{"type": "list", "items": "not a list"}]),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Article.objects.filter(slug="ny-artikkel-5").exists())

    def test_image_block_missing_src_or_alt_is_rejected(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:article_add"), {
            "title": "Ny Artikkel", "slug": "ny-artikkel-6", "ingress": "Ingress her.",
            "header_image": "", "date": "2026-02-01", "read_minutes": "3",
            "blocks_json": json.dumps([{"type": "image", "src": "foo.jpg"}]),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Article.objects.filter(slug="ny-artikkel-6").exists())

    def test_edit_form_shows_current_blocks_as_json(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:article_edit", args=[self.article.pk]))
        self.assertContains(response, "Overskrift")

    def test_valid_edit_updates_the_article(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:article_edit", args=[self.article.pk]), {
            "title": "Oppdatert Tittel", "slug": "test-artikkel", "ingress": "En kort ingress.",
            "header_image": "", "date": "2026-01-01", "read_minutes": "5",
            "blocks_json": json.dumps([{"type": "p", "text": "Ny tekst."}]),
        })
        self.assertRedirects(response, reverse("dashboard:article_edit", args=[self.article.pk]))
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Oppdatert Tittel")
        self.assertEqual(self.article.blocks, [{"type": "p", "text": "Ny tekst."}])

    def test_delete_requires_superuser(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse("dashboard:article_delete", args=[self.article.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Article.objects.filter(pk=self.article.pk).exists())

    def test_superuser_can_delete(self):
        self.client.force_login(self.superuser)
        response = self.client.post(reverse("dashboard:article_delete", args=[self.article.pk]))
        self.assertRedirects(response, reverse("dashboard:article_list"))
        self.assertFalse(Article.objects.filter(pk=self.article.pk).exists())

    def test_delete_requires_post(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("dashboard:article_delete", args=[self.article.pk]))
        self.assertEqual(response.status_code, 405)
