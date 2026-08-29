from django.db import migrations


def normalize_to_int_strings(apps, schema_editor):
    """Coerces total_leads_received/priority_score to clean numeric strings
    (blank/None/non-numeric -> "0") before the next migration converts both
    columns to PositiveIntegerField — makes that AlterField safe regardless
    of stray blank or garbage values already in the database."""
    Bedrift_info = apps.get_model("store", "Bedrift_info")
    for business in Bedrift_info.objects.all():
        update_fields = []
        for field in ("total_leads_received", "priority_score"):
            raw = getattr(business, field)
            try:
                value = int(raw)
                if value < 0:
                    value = 0
            except (TypeError, ValueError):
                value = 0
            if str(raw) != str(value):
                setattr(business, field, str(value))
                update_fields.append(field)
        if update_fields:
            business.save(update_fields=update_fields)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0010_bedrift_info_priority_score'),
    ]

    operations = [
        migrations.RunPython(normalize_to_int_strings, noop_reverse),
    ]
