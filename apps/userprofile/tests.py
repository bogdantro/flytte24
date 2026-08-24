from django.contrib.auth.models import User
from django.test import TestCase

from apps.store.models import Bedrift_info


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
