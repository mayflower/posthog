from typing import Optional, cast

from posthog.schema import (
    DataWarehouseSourceCategory,
    ExternalDataSourceType as SchemaExternalDataSourceType,
    ReleaseStatus,
    SourceConfig,
    SourceFieldInputConfig,
    SourceFieldInputConfigType,
)

from products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer import (
    BucketeerResumeConfig,
    bucketeer_source,
    check_endpoint_permissions,
    validate_credentials as validate_bucketeer_credentials,
)
from products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.settings import (
    BUCKETEER_ENDPOINTS,
    ENDPOINTS,
)
from products.warehouse_sources.backend.temporal.data_imports.sources.common.base import FieldType, ResumableSource
from products.warehouse_sources.backend.temporal.data_imports.sources.common.canonical_descriptions import (
    CanonicalDescriptions,
)
from products.warehouse_sources.backend.temporal.data_imports.sources.common.registry import SourceRegistry
from products.warehouse_sources.backend.temporal.data_imports.sources.common.resumable import ResumableSourceManager
from products.warehouse_sources.backend.temporal.data_imports.sources.common.schema import SourceSchema
from products.warehouse_sources.backend.temporal.data_imports.sources.common.typings import SourceInputs, SourceResponse
from products.warehouse_sources.backend.temporal.data_imports.sources.generated_configs.bucketeer import (
    BucketeerSourceConfig,
)
from products.warehouse_sources.backend.types import ExternalDataSourceType


@SourceRegistry.register
class BucketeerSource(ResumableSource[BucketeerSourceConfig, BucketeerResumeConfig]):
    lists_tables_without_credentials = True  # static endpoint catalog — safe for public docs

    api_docs_url = "https://docs.bucketeer.io/api-reference"

    @property
    def source_type(self) -> ExternalDataSourceType:
        return ExternalDataSourceType.BUCKETEER

    @property
    def connection_host_fields(self) -> list[str]:
        # `instance_url` is where the stored API key is sent; retargeting it must re-require
        # the key.
        return ["instance_url"]

    @property
    def get_source_config(self) -> SourceConfig:
        return SourceConfig(
            name=SchemaExternalDataSourceType.BUCKETEER,
            category=DataWarehouseSourceCategory.ENGINEERING___MONITORING,
            label="Bucketeer",
            releaseStatus=ReleaseStatus.ALPHA,
            keywords=["feature flags", "feature toggles", "experiments", "bucketeer"],
            caption="""Enter your Bucketeer instance URL and a public API key to sync your feature flags, segments, experiments, goals, audit logs, and code references into the PostHog Data warehouse.

The instance URL is your Bucketeer gateway, the host you point SDKs at. The key is an [API key](https://docs.bucketeer.io/api-reference) with a public API read role; SDK keys will not work. This connector syncs configuration for the single environment the key is bound to, so connect one source per environment.
""",
            iconPath="/static/services/bucketeer.svg",
            docsUrl="https://posthog.com/docs/cdp/sources/bucketeer",
            fields=cast(
                list[FieldType],
                [
                    SourceFieldInputConfig(
                        name="instance_url",
                        label="Instance URL",
                        type=SourceFieldInputConfigType.TEXT,
                        required=True,
                        placeholder="https://bucketeer.example.com",
                        secret=False,
                    ),
                    SourceFieldInputConfig(
                        name="api_key",
                        label="API key",
                        type=SourceFieldInputConfigType.PASSWORD,
                        required=True,
                        placeholder="",
                        secret=True,
                    ),
                ],
            ),
        )

    def get_canonical_descriptions(self) -> CanonicalDescriptions:
        from products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.canonical_descriptions import (  # noqa: PLC0415
            CANONICAL_DESCRIPTIONS,
        )

        return CANONICAL_DESCRIPTIONS

    def get_non_retryable_errors(self) -> dict[str, str | None]:
        return {
            "401 Client Error": "Your Bucketeer API key is invalid or has been disabled. Create a new key with a public API read role and reconnect.",
            "Unauthorized for url": "Your Bucketeer API key is invalid or has been disabled. Create a new key with a public API read role and reconnect.",
            "403 Client Error": "Your Bucketeer API key does not have permission to read this data. It needs a public API read role, and both the key and its environment must be enabled.",
        }

    def get_schemas(
        self,
        config: BucketeerSourceConfig,
        team_id: int,
        with_counts: bool = False,
        names: list[str] | None = None,
        force_refresh: bool = False,
        api_version: str | None = None,
    ) -> list[SourceSchema]:
        # Every table is full refresh. Bucketeer's only server-side time filters bound the
        # audit log timestamp and the experiment schedule; neither is a change-time cursor
        # that could advance an incremental sync (see settings.py).
        schemas = [
            SourceSchema(
                name=endpoint,
                supports_incremental=False,
                supports_append=False,
                incremental_fields=[],
            )
            for endpoint in ENDPOINTS
        ]
        if names is not None:
            names_set = set(names)
            schemas = [s for s in schemas if s.name in names_set]
        return schemas

    def validate_credentials(
        self,
        config: BucketeerSourceConfig,
        team_id: int,
        schema_name: Optional[str] = None,
        api_version: str | None = None,
    ) -> tuple[bool, str | None]:
        return validate_bucketeer_credentials(config.instance_url, config.api_key, schema_name, team_id)

    def get_endpoint_permissions(
        self, config: BucketeerSourceConfig, team_id: int, endpoints: list[str], api_version: str | None = None
    ) -> dict[str, str | None]:
        # A key carries one role for the whole environment, but a deployment may not expose
        # every resource, so probe each endpoint and let the picker flag unreadable tables.
        return check_endpoint_permissions(config.instance_url, config.api_key, endpoints, team_id)

    def get_resumable_source_manager(self, inputs: SourceInputs) -> ResumableSourceManager[BucketeerResumeConfig]:
        return ResumableSourceManager[BucketeerResumeConfig](inputs, BucketeerResumeConfig)

    def source_for_pipeline(
        self,
        config: BucketeerSourceConfig,
        resumable_source_manager: ResumableSourceManager[BucketeerResumeConfig],
        inputs: SourceInputs,
    ) -> SourceResponse:
        if inputs.schema_name not in BUCKETEER_ENDPOINTS:
            raise ValueError(f"Unknown Bucketeer schema '{inputs.schema_name}'")

        return bucketeer_source(
            instance_url=config.instance_url,
            api_key=config.api_key,
            endpoint=inputs.schema_name,
            team_id=inputs.team_id,
            job_id=inputs.job_id,
            resumable_source_manager=resumable_source_manager,
        )
