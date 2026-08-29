import io
import json
import tempfile

from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.leads.emails import send_receipt_email
from apps.leads.forms import WizardForm
from apps.leads.models import LeadImage, MoveLead
from apps.leads.views import MAX_PHOTO_SIZE_BYTES, _validate_photos


def _make_valid_image_upload(name="photo.jpg"):
    """Builds a real, tiny decodable JPEG wrapped in a SimpleUploadedFile — for tests that need a file that passes Pillow's Image.open().verify()."""
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, "JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")


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
        suffix = lead.reference.split("-")[-1]
        self.assertEqual(len(suffix), 8)

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

    def test_clean_rejects_the_same_business_in_two_slots(self):
        """Regression test: apps.dashboard.views.lead_assign_businesses already blocks
        this, but that guard lives only in that one view — Django's own /admin/ (a
        plain ModelAdmin with no equivalent check) could still save a MoveLead with the
        same business in two of the three slots, silently double-counting that lead in
        every per-business count the dashboard computes."""
        from apps.store.models import Bedrift_info

        business = Bedrift_info.objects.create(
            company_name="Flytt AS", email="flytt-clean-test@example.com", phone="1",
            address="A", postal_code="0001", city="Oslo", first_name="A", last_name="B",
        )
        lead = self._make_lead(business_1=business, business_2=business)
        with self.assertRaises(ValidationError):
            lead.full_clean()

    def test_clean_allows_three_distinct_businesses(self):
        from apps.store.models import Bedrift_info

        businesses = [
            Bedrift_info.objects.create(
                company_name=f"Flytt {i} AS", email=f"flytt{i}@example.com", phone="1",
                address="A", postal_code="0001", city="Oslo", first_name="A", last_name="B",
            )
            for i in range(3)
        ]
        lead = self._make_lead(business_1=businesses[0], business_2=businesses[1], business_3=businesses[2])
        lead.full_clean()  # must not raise


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

    def test_date_and_flexible_both_set_is_invalid(self):
        """Regression test: clean() used to only reject "neither set", so a bypassed POST
        sending both a real date and fleksibel=True passed validation — and
        send_receipt_email would then silently discard the date and show "Fleksibel dato"
        instead, since flyttedato/fleksibel are meant to be mutually exclusive (enforced
        client-side by the step-2 JS, which this form is the only server-side backstop for)."""
        form = WizardForm(_valid_payload(flyttedato="2026-09-12", fleksibel="on"))
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

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


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class WizardPostViewTest(TestCase):
    def test_valid_post_creates_lead_and_redirects(self):
        response = self.client.post(reverse("leads:wizard"), _valid_payload())
        self.assertRedirects(response, reverse("leads:wizard_thank_you"))
        self.assertEqual(MoveLead.objects.count(), 1)
        lead = MoveLead.objects.get()
        self.assertEqual(lead.navn, "Ola Nordmann")
        self.assertEqual(lead.flytte_type, "privat")
        # Proves the Task 5 (view) <-> Task 6 (email) seam: a real POST
        # through the view actually triggers send_receipt_email, not just a
        # direct call to send_receipt_email() in isolation.
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ola@eksempel.no"])

    def test_valid_post_with_photos_creates_lead_images(self):
        payload = _valid_payload()
        photo = _make_valid_image_upload("sofa.jpg")
        response = self.client.post(reverse("leads:wizard"), {**payload, "bilder": [photo]})
        self.assertRedirects(response, reverse("leads:wizard_thank_you"))
        lead = MoveLead.objects.get()
        self.assertEqual(lead.images.count(), 1)

    def test_invalid_post_rerenders_form_with_errors(self):
        response = self.client.post(reverse("leads:wizard"), _valid_payload(navn="O"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MoveLead.objects.count(), 0)
        self.assertTrue(response.context["form"].errors)

    def test_invalid_post_tags_the_failed_field_for_the_step_jump(self):
        """Regression test: wizard.js used to always reopen on step 1 after a bypassed-
        validation POST re-render, regardless of which step's field actually failed.
        data-error-fields is what lets it jump to the right one — assert the failing
        field name (navn, a step-5 field) actually appears there."""
        response = self.client.post(reverse("leads:wizard"), _valid_payload(navn="O"))
        self.assertContains(response, 'data-error-fields="navn"')

    def test_date_and_flexible_both_set_tags_all_for_the_step_jump(self):
        """Regression test: WizardForm.clean()'s cross-field errors attach to Django's
        NON_FIELD_ERRORS key ("__all__"), not a real field name — wizard.js's
        FIELD_TO_STEP map used to have no entry for it at all, so the step-jump
        silently no-opped and the wizard reopened on step 1 instead of step 3."""
        response = self.client.post(reverse("leads:wizard"), _valid_payload(flyttedato="2026-09-12", fleksibel="on"))
        self.assertContains(response, 'data-error-fields="__all__"')

    def test_invalid_post_repopulates_step_2_3_and_coordinate_fields(self):
        # An otherwise-valid payload with one intentionally-invalid field
        # (navn too short) should still re-render every other submitted
        # value — flytte_type/boligtype radios, the date, and the coord
        # inputs — instead of silently dropping the user's other answers.
        payload = _valid_payload(navn="O", flytte_type="bedrift", boligtype="enebolig", flyttedato="2026-10-05")
        response = self.client.post(reverse("leads:wizard"), payload)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('name="flytte_type" value="bedrift" checked', content)
        self.assertIn('name="boligtype" value="enebolig" checked', content)
        self.assertIn('value="2026-10-05"', content)

    def test_photo_that_is_not_a_real_image_is_rejected(self):
        payload = _valid_payload()
        fake_file = SimpleUploadedFile("sofa.jpg", b"fake-bytes", content_type="image/jpeg")
        response = self.client.post(reverse("leads:wizard"), {**payload, "bilder": [fake_file]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MoveLead.objects.count(), 0)
        self.assertIn("er ikke et gyldig bilde", "".join(response.context["photo_errors"]))

    def test_photo_upload_valid_real_image_is_accepted(self):
        payload = _valid_payload()
        photo = _make_valid_image_upload("sofa.jpg")
        response = self.client.post(reverse("leads:wizard"), {**payload, "bilder": [photo]})
        self.assertRedirects(response, reverse("leads:wizard_thank_you"))
        lead = MoveLead.objects.get()
        self.assertEqual(lead.images.count(), 1)

    def test_thank_you_page_returns_200(self):
        response = self.client.get(reverse("leads:wizard_thank_you"))
        self.assertEqual(response.status_code, 200)

    def test_uploaded_photo_is_stored_under_a_random_name_not_the_attacker_supplied_one(self):
        # An HTML-polyglot upload named to look like a script must never be
        # stored with that name/extension — media/ is served from the site's
        # own origin, so a same-origin "*.html" file would execute as a page.
        payload = _valid_payload()
        photo = _make_valid_image_upload("payload.html")
        response = self.client.post(reverse("leads:wizard"), {**payload, "bilder": [photo]})
        self.assertRedirects(response, reverse("leads:wizard_thank_you"))
        lead = MoveLead.objects.get()
        stored_name = lead.images.get().image.name
        self.assertNotIn("payload", stored_name)
        self.assertTrue(stored_name.endswith(".jpg"))


class ValidatePhotosTest(TestCase):
    """Unit tests on views._validate_photos — the server-side gate on request.FILES.getlist("bilder"), since accept="image/*" is client-side only."""

    def test_oversized_file_is_rejected(self):
        oversized = SimpleUploadedFile(
            "big.jpg", b"x" * (MAX_PHOTO_SIZE_BYTES + 1), content_type="image/jpeg"
        )
        errors = _validate_photos([oversized])
        self.assertEqual(len(errors), 1)
        self.assertIn("for stort", errors[0])

    def test_non_image_file_is_rejected(self):
        fake_file = SimpleUploadedFile("sofa.jpg", b"fake-bytes", content_type="image/jpeg")
        errors = _validate_photos([fake_file])
        self.assertEqual(len(errors), 1)
        self.assertIn("ikke et gyldig bilde", errors[0])

    def test_real_valid_image_passes(self):
        photo = _make_valid_image_upload("sofa.jpg")
        errors = _validate_photos([photo])
        self.assertEqual(errors, [])

    def test_too_many_files_is_rejected(self):
        photos = [_make_valid_image_upload(f"photo{i}.jpg") for i in range(21)]
        errors = _validate_photos(photos)
        self.assertEqual(len(errors), 1)
        self.assertIn("maks 20 bilder", errors[0])


class WizardTemplateRenderTest(TestCase):
    def test_renders_all_five_step_headings(self):
        response = self.client.get(reverse("leads:wizard"))
        content = response.content.decode()
        for heading in [
            "Hvor skal du flytte?",
            "Hva slags flytting er det?",
            "Når skal du flytte?",
            "Hva skal du flytte?",
            "La oss ta kontakt",
        ]:
            self.assertIn(heading, content)

    def test_renders_five_progress_segments(self):
        response = self.client.get(reverse("leads:wizard"))
        self.assertContains(response, 'class="wizard-progress__segment"', count=5)

    def test_renders_csrf_token(self):
        response = self.client.get(reverse("leads:wizard"))
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_thank_you_renders_confirmation_copy(self):
        response = self.client.get(reverse("leads:wizard_thank_you"))
        self.assertContains(response, "Forespørselen er sendt!")
        self.assertContains(response, "Tilbake til forsiden")


class ReceiptEmailTest(TestCase):
    def test_sends_one_email_to_the_lead(self):
        lead = MoveLead.objects.create(
            flytte_type="privat",
            fra="Kongens gate 1, 0153 Oslo",
            til="Storgata 14, 0184 Oslo",
            boligtype="leilighet",
            flyttedato="2026-09-12",
            navn="Ola Nordmann",
            telefon="+47 900 00 000",
            epost="ola@eksempel.no",
        )
        send_receipt_email(lead)
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, ["ola@eksempel.no"])
        self.assertEqual(sent.subject, "Vi har mottatt flytteforespørselen din")
        self.assertIn(lead.reference, sent.alternatives[0][0])
        self.assertIn("Ola Nordmann", sent.alternatives[0][0])

    def test_flexible_date_shows_fleksibel_dato_label(self):
        lead = MoveLead.objects.create(
            flytte_type="privat",
            fra="Kongens gate 1, 0153 Oslo",
            til="Storgata 14, 0184 Oslo",
            boligtype="leilighet",
            fleksibel=True,
            navn="Kari Nordmann",
            telefon="+47 900 00 000",
            epost="kari@eksempel.no",
        )
        send_receipt_email(lead)
        self.assertIn("Fleksibel dato", mail.outbox[0].alternatives[0][0])

    def test_move_date_is_rendered_in_norwegian(self):
        lead = MoveLead.objects.create(
            flytte_type="privat",
            fra="Kongens gate 1, 0153 Oslo",
            til="Storgata 14, 0184 Oslo",
            boligtype="leilighet",
            flyttedato="2026-09-12",
            navn="Ola Nordmann",
            telefon="+47 900 00 000",
            epost="ola@eksempel.no",
        )
        send_receipt_email(lead)
        self.assertIn("12. september 2026", mail.outbox[0].alternatives[0][0])
