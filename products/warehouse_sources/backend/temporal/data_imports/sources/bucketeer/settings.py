from dataclasses import dataclass


@dataclass
class BucketeerEndpointConfig:
    name: str
    # Public gateway path. Bucketeer's public API is flat under /v1.
    path: str
    # Top-level key the list of records lives under in the response body.
    data_selector: str
    # Resource-owned identifier. The connector prepends the authenticated environment id to
    # build the composite primary key, so this is only the resource half.
    id_field: str = "id"


# Public list endpoints advertised by GET /v1/export/context as contract v1 capabilities.
#
# All are full refresh. Bucketeer exposes a real server-side time filter on only two of these
# (audit_logs `from`/`to` and experiments `start_at`/`stop_at`), and neither is a change-time
# cursor: the experiment filter bounds the experiment's own schedule, not when the row last
# changed. A `created_at`/`updated_at` field in a payload is not evidence the server can filter
# on it, so nothing here advertises incremental sync.
BUCKETEER_ENDPOINTS: dict[str, BucketeerEndpointConfig] = {
    "feature_flags": BucketeerEndpointConfig(
        name="feature_flags",
        path="/v1/features",
        data_selector="features",
    ),
    "segments": BucketeerEndpointConfig(
        name="segments",
        path="/v1/segments",
        data_selector="segments",
    ),
    "experiments": BucketeerEndpointConfig(
        name="experiments",
        path="/v1/experiments",
        data_selector="experiments",
    ),
    "goals": BucketeerEndpointConfig(
        name="goals",
        path="/v1/goals",
        data_selector="goals",
    ),
    "audit_logs": BucketeerEndpointConfig(
        name="audit_logs",
        path="/v1/audit_logs",
        data_selector="auditLogs",
    ),
    "code_references": BucketeerEndpointConfig(
        name="code_references",
        path="/v1/code_references",
        data_selector="codeReferences",
    ),
}

ENDPOINTS = tuple(BUCKETEER_ENDPOINTS.keys())

# Path returning the non-secret context bound to the API key. Also the credential probe.
EXPORT_CONTEXT_PATH = "/v1/export/context"

# Contract version this connector understands. Bumped only for a breaking contract change.
SUPPORTED_CONTRACT_VERSION = "1"

# The core connector reads one environment per connection, which is what an environment API
# key is structurally bound to.
SUPPORTED_CREDENTIAL_SCOPE = "environment"

# Connector-owned lineage columns added to every row.
CONTEXT_FIELD_BY_COLUMN: dict[str, str] = {
    "bucketeer_contract_version": "contractVersion",
    "bucketeer_organization_id": "organizationId",
    "bucketeer_project_id": "projectId",
    "bucketeer_project_url_code": "projectUrlCode",
    "bucketeer_environment_id": "environmentId",
    "bucketeer_environment_name": "environmentName",
    "bucketeer_environment_url_code": "environmentUrlCode",
}

INCREMENTAL_FIELDS: dict[str, list[dict[str, str]]] = {}
