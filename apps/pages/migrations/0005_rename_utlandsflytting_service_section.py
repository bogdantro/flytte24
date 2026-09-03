"""Rename the "Utlandsflytting" services-grid item to "Distansflytting" in
already-seeded CMS content (PageSection.extra_json["items"]).

The seed command (apps.pages.management.commands.seed_home_page_sections) was
updated too, but the home page's sections are usually already in the database
by the time this ships.
"""

from django.db import migrations

OLD_TITLE = "Utlandsflytting"
NEW_TITLE = "Distansflytting"
NEW_BODY = (
    "Byråer som er vant med lange flyttelass mellom byer og landsdeler — "
    "planlegging, mellomlagring og trygg transport over store avstander."
)


def forwards(apps, schema_editor):
    PageSection = apps.get_model("pages", "PageSection")
    for section in PageSection.objects.filter(extra_json__icontains=OLD_TITLE):
        data = section.extra_json or {}
        items = data.get("items")
        if not isinstance(items, list):
            continue
        changed = False
        for item in items:
            if isinstance(item, dict) and item.get("title") == OLD_TITLE:
                item["title"] = NEW_TITLE
                item["body"] = NEW_BODY
                changed = True
        if changed:
            section.extra_json = data
            section.save(update_fields=["extra_json"])


def backwards(apps, schema_editor):
    PageSection = apps.get_model("pages", "PageSection")
    old_body = (
        "Spesialiserte byråer som håndterer toll, containere og papirarbeid. "
        "Både flytting ut av Norge og hjem igjen."
    )
    for section in PageSection.objects.filter(extra_json__icontains=NEW_TITLE):
        data = section.extra_json or {}
        items = data.get("items")
        if not isinstance(items, list):
            continue
        changed = False
        for item in items:
            if isinstance(item, dict) and item.get("title") == NEW_TITLE:
                item["title"] = OLD_TITLE
                item["body"] = old_body
                changed = True
        if changed:
            section.extra_json = data
            section.save(update_fields=["extra_json"])


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0004_page_publish_at_pagesectionrevision"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
