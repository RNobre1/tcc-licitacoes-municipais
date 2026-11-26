from django.db import migrations

from ingestion.units import normalize_unit


def backfill_unit_normalized(apps, schema_editor):
    PublicItem = apps.get_model("ingestion", "PublicItem")
    batch: list = []
    qs = PublicItem.objects.filter(unit_normalized="").exclude(unit="").iterator(chunk_size=2000)
    for item in qs:
        normalized = normalize_unit(item.unit)[:50]
        if normalized:
            item.unit_normalized = normalized
            batch.append(item)
            if len(batch) >= 2000:
                PublicItem.objects.bulk_update(batch, ["unit_normalized"])
                batch.clear()
    if batch:
        PublicItem.objects.bulk_update(batch, ["unit_normalized"])


class Migration(migrations.Migration):
    dependencies = [
        ("ingestion", "0004_publicitem_has_result"),
    ]

    operations = [
        migrations.RunPython(backfill_unit_normalized, migrations.RunPython.noop),
    ]
