from django.db import migrations


class Migration(migrations.Migration):
    """Graph node only: the upstream backfill targets enterprise data that the FOSS build does not have."""

    dependencies = [("ee", "0001_squash_2026_09_07_initial")]
    operations: list[migrations.operations.base.Operation] = []
