from django.db import migrations


class Migration(migrations.Migration):
    """Graph node only: the upstream schema addons target enterprise tables the FOSS build does not create."""

    initial = True

    dependencies = [
        ("ee", "0060_backfill_evaluation_access_control"),
        ("ee", "0061_squash_2026_09_07_finalize_fks"),
    ]
    operations: list[migrations.operations.base.Operation] = []
