from django.db import migrations


class Migration(migrations.Migration):
    """Graph node only: SCIM is an enterprise feature the FOSS build does not ship."""

    dependencies = [("ee", "0062_squash_2026_09_07_schema_addons")]
    operations: list[migrations.operations.base.Operation] = []
