import io
from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from PIL import Image

from apps.pages.models import Page, PageSection
from apps.core.models import Agency, Article
from apps.store.models import Bedrift_info, PublicBusinessInformation


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

    def test_emptying_a_list_section_does_not_revert_to_hardcoded_placeholder(self):
        """Regression test: every list-shaped section used to fall back to the
        shipped hardcoded placeholder content whenever extra_json's list was
        falsy — which an empty list [] also is. Deleting every FAQ item down
        to none (a legitimate, intentional staff action via the per-item CMS
        editor) used to instantly make the old, unreviewed placeholder
        questions go live again with no warning, because {"items": []} and
        "never customized" (no items key at all) were indistinguishable. The
        fix keys off "items" being present at all, not its truthiness."""
        page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="published"
        )
        PageSection.objects.create(
            page=page, order=8, section_type="faq", heading="Ofte stilte spørsmål",
            extra_json={"items": []},
        )
        response = self.client.get("/")
        self.assertNotContains(response, "Hva koster det å bruke Kobly?")

    def test_staff_sees_an_empty_state_hint_and_add_button_on_an_emptied_list_section(self):
        """The anonymous case above proves visitors see no placeholder leak — this
        proves staff still see something actionable (not a silently blank section)
        so they can add real content back via the per-item editor."""
        from django.contrib.auth.models import User

        staff = User.objects.create_user("staff-empty-faq", password="pw", is_staff=True)
        page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="published"
        )
        section = PageSection.objects.create(
            page=page, order=8, section_type="faq", heading="Ofte stilte spørsmål",
            extra_json={"items": []},
        )
        self.client.force_login(staff)
        response = self.client.get("/")
        self.assertContains(response, "Ingen spørsmål lagt til ennå.")
        self.assertContains(response, f'data-list-item-add data-inline-section="{section.id}"')

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

    def test_staff_sees_button_href_edit_link_next_to_the_hero_cta(self):
        from django.contrib.auth.models import User

        staff = User.objects.create_user("staffhref", password="pw", is_staff=True)
        page = Page.objects.create(title="Forside", slug="forside", path="/", template_key="home", status="published")
        section = PageSection.objects.create(page=page, order=1, section_type="hero", button_href="/spesialtilbud/")
        self.client.force_login(staff)
        response = self.client.get("/")
        self.assertContains(response, f'data-inline-section="{section.id}"')
        self.assertContains(response, 'data-inline-field="button_href"')
        self.assertContains(response, 'data-inline-current="/spesialtilbud/"')

    def test_anonymous_visitor_never_sees_the_edit_link_button(self):
        response = self.client.get("/")
        self.assertNotContains(response, "inline-edit-link-btn")

    def test_title_falls_back_to_kobly_when_no_page_exists(self):
        response = self.client.get("/")
        self.assertContains(response, "<title>Kobly</title>")

    def test_title_falls_back_to_kobly_not_the_internal_page_title(self):
        """page.title is the dashboard's "Tittel (internt navn)" field (see the
        page-settings panel in this same template) — an internal admin label,
        never meant to leak into the public <title> tag. A published home Page
        with a real title but no meta_title must still show "Kobly", not the
        internal title (this used to fall through to page.title and show
        "Forside" — the internal name every home Page starts life with)."""
        Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="published",
        )
        response = self.client.get("/")
        self.assertContains(response, "<title>Kobly</title>")
        self.assertNotContains(response, "<title>Forside</title>")


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


class ContactAndAboutPageTests(TestCase):
    """Regression tests: both pages/contact/contact.html and pages/about/about.html used to
    be completely empty stubs — {% block content %}{% endblock %} with no title override and
    no meta description, rendering as a blank page with a bare "Kobly" tab title."""

    def test_contact_page_has_a_real_title_meta_description_and_content(self):
        response = self.client.get("/contact-us/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Kontakt oss — Kobly</title>")
        self.assertContains(response, '<meta name="description" content=')
        self.assertContains(response, "hei@kobly.no")

    def test_about_page_has_a_real_title_meta_description_and_content(self):
        response = self.client.get("/about-us/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Om Kobly — Kobly</title>")
        self.assertContains(response, '<meta name="description" content=')
        self.assertContains(response, "Vi finner det beste flyttebyrået for deg")


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

    def test_blog_article_shows_wizard_cta_mid_article_and_again_at_the_end(self):
        """Matches the reference site's WizardCTA: one {type:"cta"} block embedded
        mid-article, plus a second, unconditional WizardCTA always appended at the
        very end of every article (spec §10) — so the card should appear twice."""
        response = self.client.get("/blogg/hva-er-viktig-a-tenke-pa-nar-du-skal-flytte/")
        self.assertContains(response, "Skal du flytte?", count=2)
        self.assertContains(response, "wizard-cta__button", count=2)


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

    def test_agency_detail_renders_a_real_review_date_not_blank(self):
        """Regression test: review.date is a plain "YYYY-MM-DD" string inside a JSONField,
        not a real date object, so Django's |date filter used to silently render ''
        instead of erroring — every review's date was blank on every agency page."""
        response = self.client.get("/byraer/loft/", HTTP_ACCEPT_LANGUAGE="nb")
        self.assertContains(response, "18. juli 2026")

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


class CityPageTests(TestCase):
    def test_all_5_cities_200_with_expected_title_and_h1(self):
        expected = {
            "oslo": "Oslo",
            "bergen": "Bergen",
            "trondheim": "Trondheim",
            "stavanger": "Stavanger",
            "tromso": "Tromsø",
        }
        for slug, name in expected.items():
            response = self.client.get(f"/{slug}/")
            self.assertEqual(response.status_code, 200, slug)
            self.assertContains(response, f"<title>Flyttebyrå i {name} — Kobly</title>")
            self.assertContains(response, f"Vi finner det beste flyttebyrået for deg i {name}")

    def test_unknown_city_slug_404s(self):
        response = self.client.get("/trondelag/")
        self.assertEqual(response.status_code, 404)

    def test_cta_links_carry_the_city_slug_into_the_wizard(self):
        response = self.client.get("/oslo/")
        self.assertContains(response, 'href="/flytteforesporsel/?by=oslo"')

    def test_page_includes_shared_sections(self):
        response = self.client.get("/bergen/")
        self.assertContains(response, "Slik fungerer det")
        self.assertContains(response, "Alt du trenger på ett sted")
        self.assertContains(response, "Ofte stilte spørsmål")
        self.assertContains(response, "Klar for å flytte?")

    def test_an_unrelated_single_segment_cms_page_still_reaches_render_page(self):
        """Guards against the city routes' explicit-literal-paths design regressing into a
        catch-all <slug:city_slug>/ pattern, which would swallow any other single-segment
        published Page path (e.g. a duplicated page) before it reaches render_page."""
        Page.objects.create(
            title="Forside (kopi)", slug="forside-kopi", path="/forside-kopi/",
            template_key="home", status="published",
        )
        response = self.client.get("/forside-kopi/")
        self.assertEqual(response.status_code, 200)

    def test_oslo_page_lists_all_14_districts_other_cities_do_not(self):
        """Spec §7: Oslo is the only city with sub-pages — its own page additionally
        renders a DistrictList between Services and FAQ."""
        from apps.core.districts import OSLO_DISTRICTS

        response = self.client.get("/oslo/")
        self.assertContains(response, "Bydeler i Oslo")
        for data in OSLO_DISTRICTS.values():
            self.assertContains(response, data["name"])

        response = self.client.get("/bergen/")
        self.assertNotContains(response, "Bydeler i Oslo")


class DistrictPageTests(TestCase):
    """Regression tests: spec §8's 14 Oslo district pages (/oslo/<bydel>/) were never
    built — only the 5 city pages existed. Also guards the earlier-fixed
    NoReverseMatch-riddled sitemap, which is what surfaced this gap."""

    def test_all_districts_200_with_expected_title_and_h1(self):
        from apps.core.districts import OSLO_DISTRICTS

        for slug, data in OSLO_DISTRICTS.items():
            response = self.client.get(f"/oslo/{slug}/")
            self.assertEqual(response.status_code, 200, slug)
            self.assertContains(response, f"Flyttebyrå i {data['name']} – få 3 tilbud gratis")

    def test_unknown_district_slug_404s(self):
        response = self.client.get("/oslo/ikke-en-bydel/")
        self.assertEqual(response.status_code, 404)

    def test_cta_links_to_oslo_centered_wizard_not_a_per_district_center(self):
        """Spec §8: the wizard has no per-district map center, so every district CTA
        funnels into the same Oslo-centered wizard, not a district-specific ?by=."""
        response = self.client.get("/oslo/grunerlokka/")
        self.assertContains(response, 'href="/flytteforesporsel/?by=oslo"')

    def test_breadcrumb_shows_kobly_oslo_and_the_district_name(self):
        response = self.client.get("/oslo/frogner/")
        self.assertContains(response, "Oslo")
        self.assertContains(response, "Frogner")

    def test_other_districts_list_excludes_the_current_district(self):
        response = self.client.get("/oslo/frogner/")
        self.assertContains(response, "Bjerke")
        self.assertNotContains(response, 'href="/oslo/frogner/" class="district-list__item"')

    def test_each_districts_body_paragraph_is_genuinely_unique(self):
        """Guards against the 14 pages reading as thin/duplicate SEO content — each
        district's descriptive paragraph must differ from every other district's."""
        from apps.core.districts import OSLO_DISTRICTS

        bodies = [data["body"] for data in OSLO_DISTRICTS.values()]
        self.assertEqual(len(bodies), len(set(bodies)))


class SitemapTests(TestCase):
    """Regression tests: apps/core/sitemaps.py's StaticViewsSitemap previously listed
    URL names from an unrelated car-dealership template ('sell', 'buy_car', 'verksted',
    'forsikring', etc.) that never existed in this project — every reverse() call in
    it raised NoReverseMatch, so GET /sitemap.xml 500'd unconditionally."""

    def test_sitemap_200s_instead_of_500ing(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)

    def test_sitemap_lists_static_pages_cities_districts_agencies_and_articles(self):
        # Domain-agnostic on purpose: the <loc> host comes from Django's Sites
        # framework (still the framework's default "example.com" — a separate,
        # known issue, spec §15's own "hardcoded domain" flag — not something
        # this test should hardcode a guess for either).
        call_command("seed_marketing_content", stdout=StringIO())
        response = self.client.get("/sitemap.xml")
        content = response.content.decode()
        self.assertIn("<loc>http://", content)
        self.assertIn("/</loc>", content)
        self.assertIn("/oslo/</loc>", content)
        self.assertIn("/oslo/frogner/</loc>", content)
        self.assertIn("/byraer/loft/</loc>", content)
        self.assertIn("/blogg/hva-koster-det-a-bruke-flyttebyra-i-2026/</loc>", content)


class ForBusinessPageTests(TestCase):
    def test_page_200_with_h1(self):
        response = self.client.get("/for-bedrifter/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Få flere kunder uten å konkurrere på pris")

    def test_page_contains_a_faq_question(self):
        response = self.client.get("/for-bedrifter/")
        self.assertContains(response, "Hva koster det å være partner?")

    def test_cta_links_to_real_signup_form_not_a_mailto(self):
        """Deliberate deviation from the reference site, which links its final CTA to a bare
        mailto:partner@kobly.no. This port has a real signup form + backend at
        /for-bedrifter/bli-partner/ (for_business_partner in apps/core/views.py), so the button
        must point there instead — this is the detail most likely to get silently reverted back
        to the reference's mailto: placeholder, so assert both sides explicitly."""
        response = self.client.get("/for-bedrifter/")
        self.assertContains(response, 'href="/for-bedrifter/bli-partner/"')
        self.assertNotContains(response, "mailto:partner@kobly.no")


def _make_valid_logo_upload(name="logo.jpg"):
    """Builds a real, tiny decodable JPEG wrapped in a SimpleUploadedFile — same technique
    as apps.leads.tests._make_valid_image_upload, for a file that passes ImageField validation."""
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, "JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")


def _valid_partner_payload(**overrides):
    # move_type / cities are no longer collected in the wizard (steps 1 & 2
    # were removed) — a partner sets coverage from the account portal after
    # signing up. The form still accepts them if a hand-built POST sends
    # them, but the real form never does.
    payload = {
        "company_name": "Nordisk Flyttebyrå AS",
        "company_number": "123456789",
        "employees": "12",
        "website": "https://nordisk-flytt.no",
        "address": "Storgata 1",
        "postal_code": "0153",
        "city": "Oslo",
        "first_name": "Ola",
        "last_name": "Nordmann",
        "email": "ola@nordisk-flytt.no",
        "phone": "912 34 567",
    }
    payload.update(overrides)
    return payload


class ForBusinessPartnerWizardTests(TestCase):
    """/for-bedrifter/bli-partner/ — the business-signup wizard (apps.core.views.for_business_partner)."""

    def test_get_200_shows_both_step_headings_and_drops_the_removed_ones(self):
        response = self.client.get("/for-bedrifter/bli-partner/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Om bedriften")
        self.assertContains(response, "Kontaktperson og logo")
        self.assertContains(response, "av 2")
        self.assertNotContains(response, "Hvilke tjenester tilbyr dere?")
        self.assertNotContains(response, "Hvilke byer dekker dere?")

    def test_valid_post_creates_bedrift_info_with_empty_coverage(self):
        self.client.post("/for-bedrifter/bli-partner/", _valid_partner_payload())
        self.assertEqual(Bedrift_info.objects.count(), 1)
        company = Bedrift_info.objects.get()
        # Coverage isn't asked for in the wizard anymore — set later in the portal.
        self.assertEqual(company.move_type, "")
        self.assertEqual(company.cities, "")
        self.assertEqual(company.company_name, "Nordisk Flyttebyrå AS")
        self.assertEqual(company.email, "ola@nordisk-flytt.no")

    def test_valid_post_creates_linked_public_business_information(self):
        self.client.post("/for-bedrifter/bli-partner/", _valid_partner_payload())
        company = Bedrift_info.objects.get()
        self.assertTrue(PublicBusinessInformation.objects.filter(business=company).exists())

    def test_valid_post_with_logo_attaches_it_to_public_business_information(self):
        logo = _make_valid_logo_upload()
        self.client.post("/for-bedrifter/bli-partner/", {**_valid_partner_payload(), "logo": logo})
        company = Bedrift_info.objects.get()
        self.assertTrue(company.public_info.logo.name)
        self.assertIn("business_logos/", company.public_info.logo.name)

    def test_post_missing_company_name_does_not_create_bedrift_info_and_rerenders_200(self):
        response = self.client.post("/for-bedrifter/bli-partner/", _valid_partner_payload(company_name=""))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Bedrift_info.objects.count(), 0)

    def test_invalid_post_tags_the_failed_field_for_the_step_jump(self):
        """Regression test: partner-wizard.js used to always reopen on step 1 after a
        bypassed-validation POST re-render — data-error-fields is what lets it jump to
        the step the failing field (company_name, a step-1 field) actually lives on."""
        response = self.client.post("/for-bedrifter/bli-partner/", _valid_partner_payload(company_name=""))
        self.assertContains(response, 'data-error-fields="company_name"')

    def test_firmanavn_is_wired_up_as_a_brreg_lookup(self):
        response = self.client.get("/for-bedrifter/bli-partner/")
        self.assertContains(response, "data-brreg-input")
        self.assertContains(response, "data-brreg-suggestions")

    def test_valid_post_redirects_to_thank_you_page_with_company_email_and_name(self):
        response = self.client.post("/for-bedrifter/bli-partner/", _valid_partner_payload())
        company = Bedrift_info.objects.get()
        self.assertRedirects(
            response,
            f"/for-bedrifter/soknad-sendt/?email={company.email}&company=Nordisk%20Flyttebyr%C3%A5%20AS",
            fetch_redirect_response=False,
        )

    def test_duplicate_email_is_rejected_instead_of_creating_a_second_row(self):
        """Regression test: a double-submit (double-click, browser-back-resubmit) used to
        silently create a second Bedrift_info with the same email, orphaning one of them
        forever once a later signup could only link to one via .filter(email=...).last()."""
        self.client.post("/for-bedrifter/bli-partner/", _valid_partner_payload())
        response = self.client.post("/for-bedrifter/bli-partner/", _valid_partner_payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Bedrift_info.objects.count(), 1)
        self.assertContains(response, "Det finnes allerede en søknad med denne e-postadressen.")

    def test_invalid_phone_is_rejected_server_side(self):
        """Regression test: PartnerWizardForm had no clean_phone at all, and the view saves via
        Bedrift_info.objects.create(**cleaned_data) rather than a ModelForm, so the model's own
        phone_validator never ran either — a bypassed POST could save any garbage string."""
        response = self.client.post("/for-bedrifter/bli-partner/", _valid_partner_payload(phone="x"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Bedrift_info.objects.count(), 0)

    def test_oversized_logo_is_rejected_server_side(self):
        # A real, decodable image (uncompressed BMP so size is predictable:
        # width*height*3 bytes) over the 5MB validate_max_file_size limit —
        # not just a malformed upload, so this specifically exercises the
        # size check rather than Pillow's separate "is this a real image" check.
        buffer = io.BytesIO()
        Image.new("RGB", (1500, 1500)).save(buffer, "BMP")
        buffer.seek(0)
        oversized = SimpleUploadedFile("big.bmp", buffer.read(), content_type="image/bmp")
        response = self.client.post("/for-bedrifter/bli-partner/", {**_valid_partner_payload(), "logo": oversized})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Bedrift_info.objects.count(), 0)


class PartnerWizardThankYouPageTests(TestCase):
    def test_200_and_shows_confirmation_copy(self):
        response = self.client.get("/for-bedrifter/soknad-sendt/?email=ola@nordisk-flytt.no&company=Nordisk+Flyttebyr%C3%A5+AS")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Søknaden er sendt!")

    def test_account_creation_button_carries_the_submitted_email(self):
        response = self.client.get("/for-bedrifter/soknad-sendt/?email=ola@nordisk-flytt.no&company=Nordisk+Flyttebyr%C3%A5+AS")
        self.assertContains(response, "/reg/fullfor/lag-bruker/?email=ola%40nordisk-flytt.no")

    def test_illustration_shows_the_submitted_company_name(self):
        response = self.client.get("/for-bedrifter/soknad-sendt/?email=ola@nordisk-flytt.no&company=Nordisk+Flyttebyr%C3%A5+AS")
        self.assertContains(response, "Nordisk Flyttebyrå AS")
