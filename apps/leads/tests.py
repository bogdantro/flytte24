from django.test import TestCase
from django.urls import reverse


class WizardViewSmokeTest(TestCase):
    def test_get_wizard_page_returns_200(self):
        response = self.client.get(reverse("leads:wizard"))
        self.assertEqual(response.status_code, 200)
