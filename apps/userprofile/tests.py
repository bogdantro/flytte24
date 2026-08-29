from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.leads.models import MoveLead
from apps.store.models import Bedrift_info, BusinessImage, PublicBusinessInformation, Review


def _valid_signup_payload(**overrides):
    payload = {
        "username": "ola@nordisk-flytt.no",
        "first_name": "Ola",
        "last_name": "Nordmann",
        "password1": "et-sterkt-passord-123",
        "password2": "et-sterkt-passord-123",
    }
    payload.update(overrides)
    return payload


class SignupViewTests(TestCase):
    def test_get_200_shows_the_form(self):
        response = self.client.get("/reg/fullfor/lag-bruker/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Opprett bruker")

    def test_get_prefills_username_from_email_query_param(self):
        response = self.client.get("/reg/fullfor/lag-bruker/?email=ola@nordisk-flytt.no")
        self.assertContains(response, 'value="ola@nordisk-flytt.no"')

    def test_valid_post_creates_user_and_logs_in(self):
        response = self.client.post("/reg/fullfor/lag-bruker/", _valid_signup_payload())
        self.assertRedirects(response, "/for-bedrifter/min-bruker/", fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(username="ola@nordisk-flytt.no").exists())
        # The account-creation redirect logs the new user in, so the very
        # next request should not bounce back to the login page.
        follow_up = self.client.get("/for-bedrifter/min-bruker/")
        self.assertEqual(follow_up.status_code, 200)

    def test_valid_post_links_matching_bedrift_info_by_email(self):
        company = Bedrift_info.objects.create(
            company_name="Nordisk Flyttebyrå AS",
            email="ola@nordisk-flytt.no",
            move_type="Flyttehjelp",
            cities="Oslo",
            address="Storgata 1",
            postal_code="0153",
            city="Oslo",
            first_name="Ola",
            last_name="Nordmann",
            phone="99999999",
        )
        self.client.post("/reg/fullfor/lag-bruker/?email=ola@nordisk-flytt.no", _valid_signup_payload())
        company.refresh_from_db()
        self.assertEqual(company.user, User.objects.get(username="ola@nordisk-flytt.no"))

    def test_password_mismatch_does_not_create_user_and_rerenders_200(self):
        response = self.client.post(
            "/reg/fullfor/lag-bruker/", _valid_signup_payload(password2="et-annet-passord")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="ola@nordisk-flytt.no").exists())

    def test_valid_post_sets_user_email_from_the_email_field(self):
        self.client.post("/reg/fullfor/lag-bruker/", _valid_signup_payload())
        user = User.objects.get(username="ola@nordisk-flytt.no")
        self.assertEqual(user.email, "ola@nordisk-flytt.no")

    def test_editing_the_prefilled_email_before_submit_links_by_the_edited_value(self):
        # Regression test: signup() used to re-read ?email= from the URL
        # instead of the submitted field, so editing the field before
        # submitting silently failed to link the right Bedrift_info row.
        original = Bedrift_info.objects.create(
            company_name="Feil Bedrift AS", email="feil@example.com", phone="1",
            address="A", postal_code="0001", city="Oslo", first_name="A", last_name="B",
        )
        correct = Bedrift_info.objects.create(
            company_name="Riktig Bedrift AS", email="riktig@example.com", phone="1",
            address="A", postal_code="0001", city="Oslo", first_name="A", last_name="B",
        )
        self.client.post(
            "/reg/fullfor/lag-bruker/?email=feil@example.com",
            _valid_signup_payload(username="riktig@example.com"),
        )
        user = User.objects.get(username="riktig@example.com")
        original.refresh_from_db()
        correct.refresh_from_db()
        self.assertIsNone(original.user)
        self.assertEqual(correct.user, user)


def _make_business_user(username="flytt-bruker", **overrides):
    data = dict(
        company_name="Flytt AS", email="flytt@example.com", phone="12345678",
        address="Gate 1", postal_code="0001", city="Oslo", first_name="Ola", last_name="Nordmann",
    )
    data.update(overrides)
    business = Bedrift_info.objects.create(**data)
    user = User.objects.create_user(username, password="et-sterkt-passord-123")
    business.user = user
    business.save(update_fields=["user"])
    return user, business


class CheckUserExistsEndpointRemovedTests(TestCase):
    def test_endpoint_no_longer_exists(self):
        """Regression test: /api/check-user/ was an unauthenticated, rate-limit-free
        endpoint that let anyone enumerate which emails have registered accounts by
        checking the "exists" boolean it returned. Nothing in the codebase called it
        (confirmed by repo-wide search before removal), so it was pure liability — removed
        entirely rather than just gated, since there was no real feature depending on it."""
        response = self.client.get("/api/check-user/?username=noen@example.com")
        self.assertEqual(response.status_code, 404)


class NavAuthAwarenessTests(TestCase):
    def test_anonymous_sees_login_link(self):
        response = self.client.get("/")
        self.assertContains(response, "Logg inn")
        self.assertNotContains(response, "Min side")

    def test_authenticated_partner_sees_account_and_logout_links(self):
        user, _business = _make_business_user()
        self.client.force_login(user)
        response = self.client.get("/")
        self.assertContains(response, "Min side")
        self.assertContains(response, "Logg ut")


class LoginFormTests(TestCase):
    def test_login_page_has_a_real_form(self):
        response = self.client.get("/for-bedrifter/bruker/logg-inn/")
        self.assertContains(response, "<form")
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_valid_credentials_log_in_and_redirect_to_overview(self):
        _make_business_user()
        response = self.client.post("/for-bedrifter/bruker/logg-inn/", {
            "username": "flytt-bruker", "password": "et-sterkt-passord-123",
        })
        self.assertRedirects(response, "/for-bedrifter/min-bruker/")

    def test_wrong_password_shows_error_not_a_blank_page(self):
        _make_business_user()
        response = self.client.post("/for-bedrifter/bruker/logg-inn/", {
            "username": "flytt-bruker", "password": "feil-passord",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Feil brukernavn eller passord")


class PasswordResetFlowTests(TestCase):
    def test_request_form_renders(self):
        response = self.client.get("/for-bedrifter/bruker/tilbakestill-passord/")
        self.assertContains(response, "Glemt passord")

    def test_valid_email_sends_a_reset_email(self):
        _make_business_user()
        User.objects.filter(username="flytt-bruker").update(email="flytt@example.com")
        response = self.client.post(
            "/for-bedrifter/bruker/tilbakestill-passord/", {"email": "flytt@example.com"}, follow=True
        )
        self.assertContains(response, "Sjekk e-posten din")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("tilbakestill-passord", mail.outbox[0].body)

    def test_unknown_email_does_not_error_and_sends_nothing(self):
        response = self.client.post(
            "/for-bedrifter/bruker/tilbakestill-passord/", {"email": "ukjent@example.com"}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)


class PasswordChangeTests(TestCase):
    def test_requires_login(self):
        response = self.client.get("/for-bedrifter/min-bruker/bytt-passord/")
        self.assertEqual(response.status_code, 302)

    def test_valid_change_updates_the_password(self):
        user, _business = _make_business_user()
        self.client.force_login(user)
        response = self.client.post("/for-bedrifter/min-bruker/bytt-passord/", {
            "old_password": "et-sterkt-passord-123",
            "new_password1": "et-helt-nytt-passord-456",
            "new_password2": "et-helt-nytt-passord-456",
        })
        self.assertRedirects(response, "/for-bedrifter/min-bruker/bytt-passord/fullfort/")
        self.client.logout()
        self.assertTrue(self.client.login(username="flytt-bruker", password="et-helt-nytt-passord-456"))


class MyAccountViewTests(TestCase):
    def test_requires_login(self):
        response = self.client.get("/for-bedrifter/min-bruker/")
        self.assertEqual(response.status_code, 302)

    def test_shows_pending_banner_for_inactive_business(self):
        user, _business = _make_business_user(active=False)
        self.client.force_login(user)
        response = self.client.get("/for-bedrifter/min-bruker/")
        self.assertContains(response, "Venter på godkjenning")

    def test_shows_active_badge_for_active_business(self):
        user, _business = _make_business_user(active=True)
        self.client.force_login(user)
        response = self.client.get("/for-bedrifter/min-bruker/")
        self.assertContains(response, "Aktiv")

    def test_shows_combined_pipeline_lead_count(self):
        user, business = _make_business_user(active=True, total_leads_received=2)
        MoveLead.objects.create(
            flytte_type="privat", fra="A", til="B", boligtype="leilighet",
            navn="Kari Nordmann", telefon="1", epost="k@example.com", business_1=business,
        )
        self.client.force_login(user)
        response = self.client.get("/for-bedrifter/min-bruker/")
        self.assertEqual(response.context["total_received"], 3)
        self.assertContains(response, "Kari Nordmann")

    def test_user_with_no_linked_business_sees_a_friendly_message(self):
        user = User.objects.create_user("no-business-user", password="pw")
        self.client.force_login(user)
        response = self.client.get("/for-bedrifter/min-bruker/")
        self.assertContains(response, "Ingen bedrift knyttet")


class EditPublicProfileViewTests(TestCase):
    def test_requires_login(self):
        response = self.client.get("/for-bedrifter/min-bruker/bedriftsinformasjon/")
        self.assertEqual(response.status_code, 302)

    def test_get_shows_current_values(self):
        user, business = _make_business_user()
        self.client.force_login(user)
        response = self.client.get("/for-bedrifter/min-bruker/bedriftsinformasjon/")
        self.assertContains(response, "Flytt AS")

    def test_main_form_has_multipart_enctype(self):
        """Regression test: the form has always contained the logo file input
        (public_form.logo), but was missing enctype="multipart/form-data" — a real
        browser silently omits file bytes from a non-multipart POST, so uploading a
        new logo through this form appeared to succeed ("Endringene er lagret") but
        the logo never actually changed."""
        user, _business = _make_business_user()
        self.client.force_login(user)
        response = self.client.get("/for-bedrifter/min-bruker/bedriftsinformasjon/")
        self.assertContains(response, '<form method="post" enctype="multipart/form-data">')

    def test_post_updates_core_and_public_fields(self):
        user, business = _make_business_user()
        self.client.force_login(user)
        response = self.client.post("/for-bedrifter/min-bruker/bedriftsinformasjon/", {
            "company_name": "Nytt Navn AS", "company_number": "", "employees": "",
            "phone": "87654321", "website": "", "address": "Ny gate 2", "postal_code": "0002",
            "city": "Bergen", "tiltaleform": "", "first_name": "Kari", "last_name": "Hansen",
            "cities": "Oslo, Bergen", "move_type": "Flyttehjelp",
            "about_us": "Vi flytter deg trygt.", "faq": "Spørsmål? Ring oss.",
        })
        self.assertRedirects(response, "/for-bedrifter/min-bruker/bedriftsinformasjon/")
        business.refresh_from_db()
        self.assertEqual(business.company_name, "Nytt Navn AS")
        self.assertEqual(business.phone, "87654321")
        self.assertEqual(business.public_info.about_us, "Vi flytter deg trygt.")

    def test_email_is_not_editable_from_this_form(self):
        user, business = _make_business_user()
        self.client.force_login(user)
        self.client.post("/for-bedrifter/min-bruker/bedriftsinformasjon/", {
            "company_name": "Flytt AS", "company_number": "", "employees": "",
            "phone": "12345678", "website": "", "address": "Gate 1", "postal_code": "0001",
            "city": "Oslo", "tiltaleform": "", "first_name": "Ola", "last_name": "Nordmann",
            "cities": "", "move_type": "", "about_us": "", "faq": "",
            "email": "noe-annet@example.com",  # should be ignored — not a form field
        })
        business.refresh_from_db()
        self.assertEqual(business.email, "flytt@example.com")


class BusinessImageSelfServiceTests(TestCase):
    def test_add_requires_login(self):
        response = self.client.get("/for-bedrifter/min-bruker/bilde/legg-til/")
        self.assertEqual(response.status_code, 302)

    def test_add_requires_post(self):
        user, _business = _make_business_user()
        self.client.force_login(user)
        response = self.client.get("/for-bedrifter/min-bruker/bilde/legg-til/")
        self.assertEqual(response.status_code, 405)

    def test_add_saves_an_image(self):
        user, business = _make_business_user()
        self.client.force_login(user)
        upload = SimpleUploadedFile("test.gif", b"GIF87a", content_type="image/gif")
        self.client.post("/for-bedrifter/min-bruker/bilde/legg-til/", {"image": upload})
        self.assertEqual(business.public_info.images.count(), 1)

    def test_cannot_delete_another_businesss_image(self):
        _user1, business1 = _make_business_user()
        user2, _business2 = _make_business_user(
            "annen-bruker", company_name="Annen AS", email="annen@example.com"
        )
        public_info1, _ = PublicBusinessInformation.objects.get_or_create(business=business1)
        image = BusinessImage.objects.create(
            public_info=public_info1,
            image=SimpleUploadedFile("test.gif", b"GIF87a", content_type="image/gif"),
        )
        self.client.force_login(user2)
        response = self.client.post(f"/for-bedrifter/min-bruker/bilde/{image.pk}/slett/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(BusinessImage.objects.filter(pk=image.pk).exists())


class ForesporselDatabaseViewTests(TestCase):
    def test_requires_login(self):
        response = self.client.get("/for-bedrifter/foresporsel-database/")
        self.assertEqual(response.status_code, 302)

    def test_shows_movelead_pipeline_leads_not_just_jobdistribution(self):
        user, business = _make_business_user()
        MoveLead.objects.create(
            flytte_type="privat", fra="A", til="B", boligtype="leilighet",
            navn="Per Hansen", telefon="1", epost="p@example.com", business_2=business,
        )
        self.client.force_login(user)
        response = self.client.get("/for-bedrifter/foresporsel-database/")
        self.assertContains(response, "Per Hansen")

    def test_post_updates_caps_and_redirects(self):
        user, business = _make_business_user()
        self.client.force_login(user)
        response = self.client.post("/for-bedrifter/foresporsel-database/", {
            "leads_per_day": "5", "leads_per_week": "20", "leads_per_month": "",
        })
        self.assertRedirects(response, "/for-bedrifter/foresporsel-database/")
        business.refresh_from_db()
        self.assertEqual(business.leads_per_day, "5")
        self.assertEqual(business.leads_per_week, "20")

    def test_lead_row_links_to_the_lead_detail_page(self):
        """Regression test: business_lead_entries always accepted a lead_url_resolver,
        but neither account view ever passed one and the templates never rendered
        entry.url even when it was there — a business could see a lead's reference and
        status but never its actual contact details, address, or description."""
        user, business = _make_business_user()
        lead = MoveLead.objects.create(
            flytte_type="privat", fra="A", til="B", boligtype="leilighet",
            navn="Per Hansen", telefon="1", epost="p@example.com", business_1=business,
        )
        self.client.force_login(user)
        response = self.client.get("/for-bedrifter/foresporsel-database/")
        self.assertContains(response, f'href="/for-bedrifter/min-bruker/lead/{lead.pk}/"')


class BusinessLeadDetailViewTests(TestCase):
    def setUp(self):
        self.user, self.business = _make_business_user()
        self.lead = MoveLead.objects.create(
            flytte_type="privat", fra="Storgata 1, Oslo", til="Kirkegata 2, Bergen",
            boligtype="leilighet", navn="Per Hansen", telefon="90000000",
            epost="per@example.com", beskrivelse="3 esker og en sofa",
            business_1=self.business,
        )

    def test_requires_login(self):
        response = self.client.get(f"/for-bedrifter/min-bruker/lead/{self.lead.pk}/")
        self.assertEqual(response.status_code, 302)

    def test_shows_full_lead_details(self):
        self.client.force_login(self.user)
        response = self.client.get(f"/for-bedrifter/min-bruker/lead/{self.lead.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Storgata 1, Oslo")
        self.assertContains(response, "Kirkegata 2, Bergen")
        self.assertContains(response, "Per Hansen")
        self.assertContains(response, "90000000")
        self.assertContains(response, "per@example.com")
        self.assertContains(response, "3 esker og en sofa")

    def test_a_different_businesss_user_gets_404(self):
        other_user, _other_business = _make_business_user(username="annen-bedrift", email="annen@example.com")
        self.client.force_login(other_user)
        response = self.client.get(f"/for-bedrifter/min-bruker/lead/{self.lead.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_an_archived_lead_is_not_visible(self):
        self.lead.archived = True
        self.lead.save(update_fields=["archived"])
        self.client.force_login(self.user)
        response = self.client.get(f"/for-bedrifter/min-bruker/lead/{self.lead.pk}/")
        self.assertEqual(response.status_code, 404)


class PublicBusinessProfileTests(TestCase):
    def test_shows_about_us_and_reviews(self):
        _user, business = _make_business_user(active=True)
        PublicBusinessInformation.objects.create(
            business=business, about_us="Vi er best i byen.", faq="Hvor lang tid tar det?\nCa 3 timer."
        )
        Review.objects.create(business=business, name="Kari", rating=5, comment="Utmerket service!")
        response = self.client.get(f"/bedrift/{business.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vi er best i byen.")
        self.assertContains(response, "Utmerket service!")

    def test_shows_pending_notice_for_inactive_business(self):
        # Logged in as the business's own user — an inactive profile is only
        # visible to its owner or staff (see PublicBusinessProfilePrivacyTests
        # in apps.store.tests for the access-control regression tests this
        # view's own docstring now describes).
        user, business = _make_business_user(active=False)
        self.client.force_login(user)
        response = self.client.get(f"/bedrift/{business.pk}/")
        self.assertContains(response, "ikke publisert")

    def test_anonymous_visitor_cannot_see_an_inactive_business(self):
        _user, business = _make_business_user(active=False)
        response = self.client.get(f"/bedrift/{business.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_404s_for_unknown_business(self):
        response = self.client.get("/bedrift/999999/")
        self.assertEqual(response.status_code, 404)
