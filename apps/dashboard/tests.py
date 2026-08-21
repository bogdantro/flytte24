from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.leads.models import MoveLead


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
