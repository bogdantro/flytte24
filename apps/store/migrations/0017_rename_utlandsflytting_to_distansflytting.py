"""Rename the "Utlandsflytting" service to "Distansflytting" in stored coverage.

Bedrift_info.move_type and CoverageChangeRequest.move_type are comma-separated
free-text CharFields whose allowed values are enumerated in
apps.core.forms.MOVE_TYPE_CHOICES — that list changed, so the data has to move
with it or a business's saved pill selection would silently stop matching.
"""

from django.db import migrations

OLD = "Utlandsflytting"
NEW = "Distansflytting"


def _swap(value):
    parts = [p.strip() for p in (value or "").split(",") if p.strip()]
    parts = [NEW if p == OLD else p for p in parts]
    return ", ".join(parts)


def forwards(apps, schema_editor):
    for model_name in ("Bedrift_info", "CoverageChangeRequest"):
        Model = apps.get_model("store", model_name)
        rows = Model.objects.filter(move_type__icontains=OLD)
        for row in rows:
            new_value = _swap(row.move_type)
            if new_value != row.move_type:
                row.move_type = new_value
                row.save(update_fields=["move_type"])


def backwards(apps, schema_editor):
    for model_name in ("Bedrift_info", "CoverageChangeRequest"):
        Model = apps.get_model("store", model_name)
        for row in Model.objects.filter(move_type__icontains=NEW):
            parts = [p.strip() for p in (row.move_type or "").split(",") if p.strip()]
            parts = [OLD if p == NEW else p for p in parts]
            row.move_type = ", ".join(parts)
            row.save(update_fields=["move_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0016_bedrift_info_service_areas_coveragechangerequest_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
