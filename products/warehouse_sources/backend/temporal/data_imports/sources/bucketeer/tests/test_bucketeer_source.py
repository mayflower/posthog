import pytest
from unittest import mock

from parameterized import parameterized

from posthog.schema import DataWarehouseSourceCategory, ReleaseStatus

from products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.canonical_descriptions import (
    CANONICAL_DESCRIPTIONS,
)
from products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.settings import (
    CONTEXT_FIELD_BY_COLUMN,
    ENDPOINTS,
)
from products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.source import BucketeerSource
from products.warehouse_sources.backend.temporal.data_imports.sources.common.registry import SourceRegistry
from products.warehouse_sources.backend.temporal.data_imports.sources.generated_configs.bucketeer import (
    BucketeerSourceConfig,
)
from products.warehouse_sources.backend.types import ExternalDataSourceType


class TestBucketeerSource:
    def setup_method(self) -> None:
        self.source = BucketeerSource()
        self.team_id = 123
        self.config = BucketeerSourceConfig(
            instance_url="https://bucketeer.example.com", api_key="secret-api-key-value"
        )

    def test_source_type(self) -> None:
        assert self.source.source_type == ExternalDataSourceType.BUCKETEER

    def test_registered_in_the_source_registry(self) -> None:
        assert SourceRegistry.get_source(ExternalDataSourceType.BUCKETEER) is not None

    def test_connection_host_fields_covers_instance_url(self) -> None:
        # The stored API key is sent to whatever `instance_url` points at, so retargeting the
        # URL must force the editor to re-enter the key.
        assert self.source.connection_host_fields == ["instance_url"]

    def test_ships_visible_as_alpha(self) -> None:
        config = self.source.get_source_config
        assert config.releaseStatus == ReleaseStatus.ALPHA
        assert config.category == DataWarehouseSourceCategory.ENGINEERING___MONITORING
        # unreleasedSource hides the connector from every user.
        assert not config.unreleasedSource

    def test_api_key_field_is_marked_secret(self) -> None:
        fields = {f.name: f for f in self.source.get_source_config.fields}
        assert fields["api_key"].secret is True
        assert fields["instance_url"].secret is False

    def test_get_schemas_covers_all_endpoints_as_full_refresh(self) -> None:
        schemas = self.source.get_schemas(self.config, self.team_id)
        assert {s.name for s in schemas} == set(ENDPOINTS)
        assert all(s.supports_incremental is False for s in schemas)
        assert all(s.supports_append is False for s in schemas)
        assert all(s.incremental_fields == [] for s in schemas)

    def test_get_schemas_filtered_by_names(self) -> None:
        schemas = self.source.get_schemas(self.config, self.team_id, names=["feature_flags"])
        assert len(schemas) == 1
        assert schemas[0].name == "feature_flags"

    def test_get_schemas_filtered_unknown_name_returns_empty(self) -> None:
        assert self.source.get_schemas(self.config, self.team_id, names=["nope"]) == []

    def test_documented_tables_render_for_public_docs(self) -> None:
        tables = self.source.get_documented_tables()
        assert {t["name"] for t in tables} == set(ENDPOINTS)
        assert all("Full refresh" in t["sync_methods"] for t in tables)

    def test_every_table_has_a_canonical_description(self) -> None:
        assert set(CANONICAL_DESCRIPTIONS.keys()) == set(ENDPOINTS)

    def test_every_table_documents_the_injected_lineage_columns(self) -> None:
        # These columns exist on every row, so a reader of any table needs them described.
        for table, entry in CANONICAL_DESCRIPTIONS.items():
            for column in CONTEXT_FIELD_BY_COLUMN:
                assert column in entry["columns"], f"{table} is missing {column}"

    @parameterized.expand(
        [
            ("401 Client Error: Unauthorized for url: https://bucketeer.example.com/v1/features",),
            ("403 Client Error: Forbidden for url: https://bucketeer.example.com/v1/audit_logs",),
        ]
    )
    def test_non_retryable_errors_match_auth_failures(self, observed_error: str) -> None:
        non_retryable = self.source.get_non_retryable_errors()
        assert any(key in observed_error for key in non_retryable)

    @parameterized.expand(
        [
            ("500 Server Error: Internal Server Error for url: https://bucketeer.example.com/v1/features",),
            ("429 Client Error: Too Many Requests for url: https://bucketeer.example.com/v1/goals",),
        ]
    )
    def test_non_retryable_errors_ignore_transient(self, unrelated_error: str) -> None:
        non_retryable = self.source.get_non_retryable_errors()
        assert not any(key in unrelated_error for key in non_retryable)

    @mock.patch(
        "products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.source.check_endpoint_permissions"
    )
    def test_get_endpoint_permissions_delegates_to_shared_helper(self, mock_check: mock.MagicMock) -> None:
        mock_check.return_value = {"audit_logs": "no permission", "feature_flags": None}
        result = self.source.get_endpoint_permissions(self.config, self.team_id, ["audit_logs", "feature_flags"])
        assert result == {"audit_logs": "no permission", "feature_flags": None}
        mock_check.assert_called_once_with(
            "https://bucketeer.example.com", "secret-api-key-value", ["audit_logs", "feature_flags"], self.team_id
        )

    @mock.patch("products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.source.bucketeer_source")
    def test_source_for_pipeline_plumbs_arguments(self, mock_source: mock.MagicMock) -> None:
        inputs = mock.MagicMock()
        inputs.schema_name = "feature_flags"
        inputs.team_id = self.team_id
        inputs.job_id = "job-123"
        manager = mock.MagicMock()

        self.source.source_for_pipeline(self.config, manager, inputs)

        mock_source.assert_called_once()
        kwargs = mock_source.call_args.kwargs
        assert kwargs["instance_url"] == "https://bucketeer.example.com"
        assert kwargs["api_key"] == "secret-api-key-value"
        assert kwargs["endpoint"] == "feature_flags"
        assert kwargs["team_id"] == self.team_id
        assert kwargs["job_id"] == "job-123"
        assert kwargs["resumable_source_manager"] is manager

    def test_source_for_pipeline_rejects_unknown_schema(self) -> None:
        inputs = mock.MagicMock()
        inputs.schema_name = "nope"
        with pytest.raises(ValueError, match="Unknown Bucketeer schema"):
            self.source.source_for_pipeline(self.config, mock.MagicMock(), inputs)
