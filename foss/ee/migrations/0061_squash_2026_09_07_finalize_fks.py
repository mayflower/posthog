import django.db.models.deletion
from django.db import migrations, models

from posthog.migration_helpers.squash_idempotent import AddConstraintIfMissing, AddFieldIfMissing


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("ee", "0001_squash_2026_09_07_initial"),
        ("feature_flags", "0001_squash_2026_09_07_initial"),
    ]

    operations = [
        AddFieldIfMissing(
            model_name="featureflagroleaccess",
            name="feature_flag",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="access",
                related_query_name="access",
                to="feature_flags.featureflag",
            ),
        ),
        AddConstraintIfMissing(
            model_name="featureflagroleaccess",
            constraint=models.UniqueConstraint(fields=("role", "feature_flag"), name="unique_feature_flag_and_role"),
        ),
    ]
