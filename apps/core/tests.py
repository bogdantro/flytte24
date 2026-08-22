from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.pages.models import Page, PageSection
from apps.core.models import Agency, Article


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

    def test_seeded_how_it_works_steps_still_show_illustrations(self):
        call_command("seed_home_page_sections", stdout=StringIO())
        response = self.client.get("/")
        self.assertContains(response, "howitworks-1-skjema.png")

    def test_seeded_testimonials_still_show_photos(self):
        call_command("seed_home_page_sections", stdout=StringIO())
        response = self.client.get("/")
        self.assertContains(response, "ciocan-ciprian-_Z2eTqGL7dg-unsplash.jpg")

    def test_meta_title_and_description_render_when_set(self):
        page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="published",
            meta_title="Egendefinert SEO-tittel", meta_description="Egendefinert SEO-beskrivelse.",
        )
        response = self.client.get("/")
        self.assertContains(response, "<title>Egendefinert SEO-tittel</title>")
        self.assertContains(response, '<meta name="description" content="Egendefinert SEO-beskrivelse.">')

    def test_title_falls_back_to_page_title_then_kobly(self):
        response = self.client.get("/")
        self.assertContains(response, "<title>Kobly</title>")


class RenderPageViewTests(TestCase):
    def test_published_non_home_path_renders(self):
        page = Page.objects.create(
            title="Forside (kopi)", slug="forside-kopi", path="/forside-kopi/",
            template_key="home", status="published",
        )
        PageSection.objects.create(page=page, order=1, section_type="hero", heading="Kopiert overskrift")
        response = self.client.get("/forside-kopi/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kopiert overskrift")

    def test_draft_non_home_path_404s_for_anonymous(self):
        Page.objects.create(
            title="Utkast", slug="utkast-side", path="/utkast-side/",
            template_key="home", status="draft",
        )
        response = self.client.get("/utkast-side/")
        self.assertEqual(response.status_code, 404)

    def test_draft_non_home_path_renders_for_staff(self):
        from django.contrib.auth.models import User

        staff = User.objects.create_user("staffcore", password="pw", is_staff=True)
        Page.objects.create(
            title="Utkast", slug="utkast-side", path="/utkast-side/",
            template_key="home", status="draft",
        )
        self.client.force_login(staff)
        response = self.client.get("/utkast-side/")
        self.assertEqual(response.status_code, 200)

    def test_unknown_path_404s(self):
        response = self.client.get("/dette-finnes-ikke/")
        self.assertEqual(response.status_code, 404)

    def test_non_home_template_key_404s_even_if_published(self):
        Page.objects.create(
            title="Om oss", slug="om-oss", path="/om-oss/",
            template_key="about", status="published",
        )
        response = self.client.get("/om-oss/")
        self.assertEqual(response.status_code, 404)


class BlogPageTests(TestCase):
    def setUp(self):
        call_command("seed_marketing_content", stdout=StringIO())

    def test_blog_index_200_lists_both_article_titles(self):
        response = self.client.get("/blogg/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hva er viktig å tenke på når du skal flytte?")
        self.assertContains(response, "Hva koster det å bruke flyttebyrå i 2026?")

    def test_blog_article_200_shows_real_block_content(self):
        response = self.client.get("/blogg/hva-er-viktig-a-tenke-pa-nar-du-skal-flytte/")
        self.assertEqual(response.status_code, 200)
        # h2 block
        self.assertContains(response, "Seks uker før: ta de store valgene")
        # p block
        self.assertContains(response, "De fleste undervurderer ikke selve flyttedagen")

    def test_blog_article_404s_on_unknown_slug(self):
        response = self.client.get("/blogg/dette-finnes-ikke/")
        self.assertEqual(response.status_code, 404)


class AgencyPageTests(TestCase):
    def setUp(self):
        call_command("seed_marketing_content", stdout=StringIO())

    def test_agency_list_200_lists_all_four_agency_names(self):
        response = self.client.get("/byraer/")
        self.assertEqual(response.status_code, 200)
        for name in ["LØFT", "relok.", "Flyttefoten", "Flytteby"]:
            self.assertContains(response, name)

    def test_agency_detail_200_shows_tagline_services_and_a_review(self):
        response = self.client.get("/byraer/loft/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Flytting med hodet, ikke bare ryggen")
        self.assertContains(response, "Piano og flygel")
        self.assertContains(response, "hele leiligheten var nede på tre timer")

    def test_agency_detail_404s_on_unknown_slug(self):
        response = self.client.get("/byraer/dette-finnes-ikke/")
        self.assertEqual(response.status_code, 404)


class SeedMarketingContentCommandTests(TestCase):
    def test_seed_creates_four_agencies_and_three_articles(self):
        call_command("seed_marketing_content", stdout=StringIO())
        self.assertEqual(Agency.objects.count(), 4)
        self.assertEqual(Article.objects.count(), 3)

    def test_seed_run_twice_does_not_duplicate(self):
        call_command("seed_marketing_content", stdout=StringIO())
        call_command("seed_marketing_content", stdout=StringIO())
        self.assertEqual(Agency.objects.count(), 4)
        self.assertEqual(Article.objects.count(), 3)
