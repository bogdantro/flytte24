from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.pages.models import Page, PageSection


class PageModelTests(TestCase):
    def test_str_is_title(self):
        page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home"
        )
        self.assertEqual(str(page), "Forside")

    def test_slug_must_be_unique(self):
        Page.objects.create(title="Forside", slug="forside", path="/", template_key="home")
        with self.assertRaises(Exception):
            Page.objects.create(
                title="Forside 2", slug="forside", path="/annen-sti/", template_key="about"
            )

    def test_defaults_to_draft(self):
        page = Page.objects.create(title="Om oss", slug="om-oss", path="/om-oss/", template_key="about")
        self.assertEqual(page.status, "draft")


class PageSectionModelTests(TestCase):
    def setUp(self):
        self.page = Page.objects.create(
            title="Forside", slug="forside", path="/", template_key="home", status="published"
        )

    def test_ordered_by_order_field(self):
        second = PageSection.objects.create(page=self.page, order=2, section_type="faq")
        first = PageSection.objects.create(page=self.page, order=1, section_type="hero")
        self.assertEqual(list(self.page.sections.all()), [first, second])

    def test_extra_json_defaults_to_empty_dict(self):
        section = PageSection.objects.create(page=self.page, order=1, section_type="faq")
        self.assertEqual(section.extra_json, {})

    def test_extra_json_round_trips_nested_lists(self):
        section = PageSection.objects.create(
            page=self.page,
            order=1,
            section_type="faq",
            extra_json={"items": [{"question": "Q?", "answer": "A."}]},
        )
        section.refresh_from_db()
        self.assertEqual(section.extra_json["items"][0]["question"], "Q?")


class SeedHomePageSectionsCommandTests(TestCase):
    def test_creates_page_and_eight_sections(self):
        call_command("seed_home_page_sections", stdout=StringIO())
        page = Page.objects.get(template_key="home")
        self.assertEqual(page.status, "published")
        self.assertEqual(page.sections.count(), 8)
        self.assertEqual(
            list(page.sections.values_list("section_type", flat=True)),
            ["hero", "stats", "how_it_works", "testimonials", "trust", "services", "cities", "faq"],
        )

    def test_idempotent_on_second_run(self):
        call_command("seed_home_page_sections", stdout=StringIO())
        call_command("seed_home_page_sections", stdout=StringIO())
        self.assertEqual(Page.objects.filter(template_key="home").count(), 1)
        self.assertEqual(PageSection.objects.count(), 8)

    def test_hero_heading_matches_current_hardcoded_copy(self):
        call_command("seed_home_page_sections", stdout=StringIO())
        hero = Page.objects.get(template_key="home").sections.get(section_type="hero")
        self.assertEqual(hero.heading, "Vi finner det beste flyttebyrået for deg")
