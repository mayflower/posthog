# FOSS build: creates only the MIT access-control models that carry the "ee" app label
# (products/access_control/backend/models). Node names mirror the upstream migration graph so
# core migrations that depend on "ee" nodes keep resolving.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import posthog.uuidt


class Migration(migrations.Migration):
    replaces = [
        ("ee", "0001_initial"),
        ("ee", "0002_hook"),
        ("ee", "0003_license_max_users"),
        ("ee", "0004_enterpriseeventdefinition_enterprisepropertydefinition"),
        ("ee", "0005_project_based_permissioning"),
        ("ee", "0006_event_definition_verification"),
        ("ee", "0007_dashboard_permissions"),
        ("ee", "0008_null_definition_descriptions"),
        ("ee", "0009_deprecated_old_tags"),
        ("ee", "0010_migrate_definitions_tags"),
        ("ee", "0011_add_tags_back"),
        ("ee", "0012_migrate_tags_v2"),
        ("ee", "0013_silence_deprecated_tags_warnings"),
        ("ee", "0014_roles_memberships_and_resource_access"),
        ("ee", "0015_add_verified_properties"),
        ("ee", "0016_rolemembership_organization_member"),
        ("ee", "0017_accesscontrol_and_more"),
        ("ee", "0018_conversation_conversationcheckpoint_and_more"),
        ("ee", "0019_remove_conversationcheckpointblob_unique_checkpoint_blob_and_more"),
        ("ee", "0020_corememory"),
        ("ee", "0021_conversation_status"),
        ("ee", "0022_enterpriseeventdefinition_default_columns"),
        ("ee", "0022_enterpriseeventdefinition_hidden_and_more"),
        ("ee", "0023_merge_20250312_0732"),
        ("ee", "0024_conversation_type"),
        ("ee", "0025_role_members"),
        ("ee", "0026_conversation_created_at_conversation_title_and_more"),
        ("ee", "0027_add_single_session_summary_model"),
        ("ee", "0028_alter_conversation_type"),
        ("ee", "0029_llmtracesummary_llmtracesummary_unique_trace_summary"),
        ("ee", "0030_singlesessionsummary_distinct_id_and_more"),
        ("ee", "0031_agentartifact"),
        ("ee", "0032_scimprovisioneduser_and_more"),
        ("ee", "0033_conversation_type_slack"),
        ("ee", "0034_conversation_slack_fields"),
        ("ee", "0035_conversation_slack_index"),
        ("ee", "0036_add_is_internal_to_conversation"),
        ("ee", "0037_add_conversation_approval_decisions"),
        ("ee", "0038_alter_enterpriseeventdefinition_eventdefinition_ptr_and_more"),
        ("ee", "0039_add_sandbox_fields_to_conversation"),
        ("ee", "0040_scimrequestlog"),
        ("ee", "0041_migrate_dashboards_models"),
        ("ee", "0042_team_session_summaries_config"),
        ("ee", "0043_teamsessionsummariesconfig_custom_tags"),
        ("ee", "0044_conversation_deleted_conversation_deleted_at"),
        ("ee", "0045_migrate_feature_flags_models"),
        ("ee", "0046_migrate_cdp_models"),
        ("ee", "0047_migrate_ai_observability_models"),
        ("ee", "0048_migrate_posthog_ai_models"),
        ("ee", "0049_migrate_posthog_ai_models"),
        ("ee", "0050_migrate_replay_models"),
        ("ee", "0051_backfill_ai_observability_clusters_access_control"),
        ("ee", "0052_backfill_llm_skill_access_control"),
        ("ee", "0053_backfill_tagger_access_control"),
        ("ee", "0054_backfill_llm_playground_access_control"),
        ("ee", "0055_scim_records_identity_provider_config"),
        ("ee", "0056_scim_records_organization_domain_nullable"),
        ("ee", "0057_scim_records_identity_provider_config_indexes"),
        ("ee", "0058_backfill_scim_provisioned_user_config"),
        ("ee", "0059_scimprovisioneduser_unique_config"),
    ]

    initial = True

    dependencies = [
        ("dashboards", "0015_dashboard_customization"),
        ("event_definitions", "0009_drop_eventproperty_proj_event_coalesce_idx"),
        ("posthog", "1340_drop_userproductlist_reason_columns"),
    ]

    operations = [
        migrations.CreateModel(
            name="Role",
            fields=[
                (
                    "id",
                    models.UUIDField(default=posthog.uuidt.UUIDT, editable=False, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "feature_flags_access_level",
                    models.PositiveSmallIntegerField(
                        choices=[(21, "Can only view"), (37, "Can always edit")], default=37
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="roles",
                        related_query_name="role",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="roles",
                        related_query_name="role",
                        to="posthog.organization",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RoleMembership",
            fields=[
                (
                    "id",
                    models.UUIDField(default=posthog.uuidt.UUIDT, editable=False, primary_key=True, serialize=False),
                ),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "organization_member",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_memberships",
                        related_query_name="role_membership",
                        to="posthog.organizationmembership",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="roles",
                        related_query_name="role",
                        to="ee.role",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_memberships",
                        related_query_name="role_membership",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="role",
            name="members",
            field=models.ManyToManyField(through="ee.RoleMembership", to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name="OrganizationResourceAccess",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "resource",
                    models.CharField(
                        choices=[
                            ("feature flags", "feature flags"),
                            ("experiments", "experiments"),
                            ("cohorts", "cohorts"),
                            ("data management", "data management"),
                            ("session recordings", "session recordings"),
                            ("insights", "insights"),
                            ("dashboards", "dashboards"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "access_level",
                    models.PositiveSmallIntegerField(
                        choices=[(21, "Can only view"), (37, "Can always edit")], default=37
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="organization_resource_access",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="resource_access",
                        to="posthog.organization",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AccessControl",
            fields=[
                (
                    "id",
                    models.UUIDField(default=posthog.uuidt.UUIDT, editable=False, primary_key=True, serialize=False),
                ),
                ("access_level", models.CharField(max_length=32)),
                ("resource", models.CharField(max_length=32)),
                ("resource_id", models.CharField(max_length=36, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="access_controls",
                        related_query_name="access_controls",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organization_member",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_controls",
                        related_query_name="access_controls",
                        to="posthog.organizationmembership",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_controls",
                        related_query_name="access_controls",
                        to="ee.role",
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_controls",
                        related_query_name="access_controls",
                        to="posthog.team",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FeatureFlagRoleAccess",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="feature_flag_access",
                        related_query_name="feature_flag_access",
                        to="ee.role",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="role",
            constraint=models.UniqueConstraint(fields=("organization", "name"), name="unique_role_name"),
        ),
        migrations.AddConstraint(
            model_name="rolemembership",
            constraint=models.UniqueConstraint(fields=("role", "user"), name="unique_user_and_role"),
        ),
        migrations.AddConstraint(
            model_name="organizationresourceaccess",
            constraint=models.UniqueConstraint(
                fields=("organization", "resource"), name="unique resource per organization"
            ),
        ),
        migrations.AddConstraint(
            model_name="accesscontrol",
            constraint=models.UniqueConstraint(
                fields=("resource", "resource_id", "team", "organization_member", "role"),
                name="unique resource per target",
            ),
        ),
    ]
