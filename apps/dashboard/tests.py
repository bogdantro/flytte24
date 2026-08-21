from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.leads.models import MoveLead
from apps.pages.models import Page, PageSection
from apps.store.models import Bedrift_info, BusinessImage, PublicBusinessInformation


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

    def test_login_with_valid_staff_credentials_redirects_to_list(self):
        response = self.client.post(
            reverse("dashboard:login"),
            {"username": "staffuser", "password": "secret-pw-123"},
        )
        self.assertRedirects(response, reverse("dashboard:lead_list"))

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
        self.assertEqual(response.context["leads"].get().pk, contacted.pk)

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

    def test_delete_lead_removes_it(self):
        lead = _make_lead()
        response = self.client.post(reverse("dashboard:delete_lead", args=[lead.pk]))
        self.assertRedirects(response, reverse("dashboard:lead_list"))
        self.assertEqual(MoveLead.objects.filter(pk=lead.pk).count(), 0)

    def test_delete_requires_post(self):
        lead = _make_lead()
        response = self.client.get(reverse("dashboard:delete_lead", args=[lead.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(MoveLead.objects.filter(pk=lead.pk).count(), 1)


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


class PageEditViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff3", password="pw", is_staff=True)
        self.page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="draft"
        )
        self.section = PageSection.objects.create(
            page=self.page, order=1, section_type="hero", heading="Original overskrift"
        )

    def test_requires_staff_login(self):
        url = reverse("dashboard:page_edit", args=[self.page.pk])
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('dashboard:login')}?next={url}")

    def test_get_shows_current_values(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("dashboard:page_edit", args=[self.page.pk]))
        self.assertContains(response, "Original overskrift")

    def test_post_updates_page_and_section_and_sets_updated_by(self):
        self.client.force_login(self.staff)
        url = reverse("dashboard:page_edit", args=[self.page.pk])
        response = self.client.post(url, {
            "title": "Forside",
            "path": "/",
            "status": "published",
            f"section-{self.section.pk}-heading": "Ny overskrift",
            f"section-{self.section.pk}-subheading": "",
            f"section-{self.section.pk}-body_text": "",
            f"section-{self.section.pk}-button_label": "",
            f"section-{self.section.pk}-button_href": "",
        })
        self.assertRedirects(response, url)
        self.page.refresh_from_db()
        self.section.refresh_from_db()
        self.assertEqual(self.page.status, "published")
        self.assertEqual(self.page.updated_by, self.staff)
        self.assertEqual(self.section.heading, "Ny overskrift")


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
        self.assertRedirects(response, reverse("dashboard:page_edit", args=[clone.pk]))
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


class PageDeleteViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff5", password="pw", is_staff=True)
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


class BusinessDetailViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff7", password="pw", is_staff=True)
        self.business = Bedrift_info.objects.create(
            company_name="Flytt AS", email="flytt@example.com", phone="12345678",
            address="Gate 1", postal_code="0001", city="Oslo",
            first_name="Ola", last_name="Nordmann", active=False,
            total_leads_received="7",
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
        self.assertEqual(self.business.priority_score, "8")
        self.assertFalse(self.business.active)
        self.assertEqual(self.business.total_leads_received, "7")
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


class BusinessImageViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff9", password="pw", is_staff=True)
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
        self.client.post(reverse("dashboard:business_image_add", args=[self.business.pk]), {"image": upload})
        self.assertEqual(self.public_info.images.count(), 6)

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
