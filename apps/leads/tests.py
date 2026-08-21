from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.leads.models import LeadImage, MoveLead


class WizardViewSmokeTest(TestCase):
    def test_get_wizard_page_returns_200(self):
        response = self.client.get(reverse("leads:wizard"))
        self.assertEqual(response.status_code, 200)


class MoveLeadModelTest(TestCase):
    def _make_lead(self, **overrides):
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

    def test_reference_is_generated_on_save(self):
        lead = self._make_lead()
        self.assertTrue(lead.reference.startswith(f"KOB-{lead.created_at.year}-"))
        self.assertTrue(lead.reference.endswith(str(lead.pk)))

    def test_str_includes_reference_and_name(self):
        lead = self._make_lead()
        self.assertIn(lead.reference, str(lead))
        self.assertIn("Ola Nordmann", str(lead))

    def test_lead_image_attaches_to_lead(self):
        lead = self._make_lead()
        image = LeadImage.objects.create(
            lead=lead,
            image=SimpleUploadedFile("sofa.jpg", b"fake-image-bytes", content_type="image/jpeg"),
        )
        self.assertEqual(lead.images.count(), 1)
        self.assertEqual(lead.images.first(), image)
