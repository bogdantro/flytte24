import json
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.leads.forms import WizardForm
from apps.leads.models import LeadImage, MoveLead


class WizardViewSmokeTest(TestCase):
    def test_get_wizard_page_returns_200(self):
        response = self.client.get(reverse("leads:wizard"))
        self.assertEqual(response.status_code, 200)


class WizardGetViewTest(TestCase):
    def test_fra_query_param_prefills_form(self):
        response = self.client.get(reverse("leads:wizard"), {"fra": "1170"})
        self.assertContains(response, 'value="1170"')

    def test_by_query_param_sets_initial_center(self):
        response = self.client.get(reverse("leads:wizard"), {"by": "bergen"})
        center = json.loads(response.context["initial_center_json"])
        self.assertEqual(center["lat"], 60.3913)
        self.assertEqual(center["zoom"], 11)

    def test_unknown_by_query_param_is_ignored(self):
        response = self.client.get(reverse("leads:wizard"), {"by": "narnia"})
        self.assertEqual(response.context["initial_center_json"], "null")

    def test_no_by_query_param_gives_null_center(self):
        response = self.client.get(reverse("leads:wizard"))
        self.assertEqual(response.context["initial_center_json"], "null")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
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


def _valid_payload(**overrides):
    data = dict(
        flytte_type="privat",
        fra="Kongens gate 1, 0153 Oslo",
        fra_lat="59.913",
        fra_lon="10.752",
        til="Storgata 14, 0184 Oslo",
        til_lat="",
        til_lon="",
        boligtype="leilighet",
        flyttedato="2026-09-12",
        fleksibel="",
        beskrivelse="3-seters sofa",
        navn="Ola Nordmann",
        telefon="+47 900 00 000",
        epost="ola@eksempel.no",
    )
    data.update(overrides)
    return data


class WizardFormTest(TestCase):
    def test_valid_payload_passes(self):
        form = WizardForm(_valid_payload())
        self.assertTrue(form.is_valid(), form.errors)

    def test_fra_shorter_than_3_chars_is_invalid(self):
        form = WizardForm(_valid_payload(fra="Os"))
        self.assertFalse(form.is_valid())
        self.assertIn("fra", form.errors)

    def test_til_shorter_than_3_chars_is_invalid(self):
        form = WizardForm(_valid_payload(til="St"))
        self.assertFalse(form.is_valid())
        self.assertIn("til", form.errors)

    def test_coordinates_are_optional(self):
        form = WizardForm(_valid_payload(fra_lat="", fra_lon="", til_lat="", til_lon=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_flytte_type_is_invalid(self):
        form = WizardForm(_valid_payload(flytte_type=""))
        self.assertFalse(form.is_valid())
        self.assertIn("flytte_type", form.errors)

    def test_missing_boligtype_is_invalid(self):
        form = WizardForm(_valid_payload(boligtype=""))
        self.assertFalse(form.is_valid())
        self.assertIn("boligtype", form.errors)

    def test_missing_date_and_not_flexible_is_invalid(self):
        form = WizardForm(_valid_payload(flyttedato="", fleksibel=""))
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_flexible_without_date_is_valid(self):
        form = WizardForm(_valid_payload(flyttedato="", fleksibel="on"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_beskrivelse_is_always_optional(self):
        form = WizardForm(_valid_payload(beskrivelse=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_navn_single_char_is_invalid(self):
        form = WizardForm(_valid_payload(navn="O"))
        self.assertFalse(form.is_valid())
        self.assertIn("navn", form.errors)

    def test_telefon_too_short_is_invalid(self):
        form = WizardForm(_valid_payload(telefon="123"))
        self.assertFalse(form.is_valid())
        self.assertIn("telefon", form.errors)

    def test_telefon_allows_spaces_and_plus(self):
        form = WizardForm(_valid_payload(telefon="+47 900 00 000"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_epost_without_at_sign_is_invalid(self):
        form = WizardForm(_valid_payload(epost="ikke-en-epost"))
        self.assertFalse(form.is_valid())
        self.assertIn("epost", form.errors)

    def test_epost_permissive_pattern_accepts_short_domain(self):
        # Spec §5.9: /\S+@\S+\.\S+/ — permissive, not RFC-strict.
        form = WizardForm(_valid_payload(epost="a@b.co"))
        self.assertTrue(form.is_valid(), form.errors)
