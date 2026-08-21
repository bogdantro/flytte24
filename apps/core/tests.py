from django.test import TestCase

from apps.pages.models import Page, PageSection


class HomePageRenderingTests(TestCase):
    def test_renders_hardcoded_copy_with_zero_page_rows(self):
        response = self.client.get("/")
        self.assertContains(response, "Vi finner det beste flyttebyrået for deg")
        self.assertContains(response, "Hva sier kundene våre?")

    def test_renders_seeded_section_copy_when_published(self):
        page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="published"
        )
        PageSection.objects.create(
            page=page, order=1, section_type="hero", heading="Egendefinert overskrift"
        )
        response = self.client.get("/")
        self.assertContains(response, "Egendefinert overskrift")
        # The hero's default heading text also appears verbatim, independently,
        # in the site-wide footer blurb (core/footer.html, unrelated to Page/
        # PageSection and unaffected by this override). Assert it now appears
        # exactly once (from the footer) instead of twice (hero + footer),
        # proving the hero section itself no longer renders its hardcoded
        # default rather than asserting total absence from the page.
        self.assertContains(response, "Vi finner det beste flyttebyrået for deg", count=1)

    def test_draft_page_does_not_override_hardcoded_copy(self):
        page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="draft"
        )
        PageSection.objects.create(
            page=page, order=1, section_type="hero", heading="Skal ikke vises"
        )
        response = self.client.get("/")
        self.assertContains(response, "Vi finner det beste flyttebyrået for deg")
        self.assertNotContains(response, "Skal ikke vises")

    def test_faq_extra_json_list_overrides_hardcoded_items(self):
        page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="published"
        )
        PageSection.objects.create(
            page=page,
            order=8,
            section_type="faq",
            heading="Ofte stilte spørsmål",
            extra_json={"items": [{"question": "Egendefinert spørsmål?", "answer": "Egendefinert svar."}]},
        )
        response = self.client.get("/")
        self.assertContains(response, "Egendefinert spørsmål?")
        self.assertNotContains(response, "Hva koster det å bruke Kobly?")
