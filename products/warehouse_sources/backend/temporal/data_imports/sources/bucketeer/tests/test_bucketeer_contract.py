# The fixtures are byte-for-byte copies of Bucketeer's, kept in step by
# sync_bucketeer_contract_fixtures.py. Running the real source against them means a change
# to a Bucketeer response shape fails here rather than in a production sync.
#
# No sibling Bucketeer checkout is needed: this reads the checked-in copies, so ordinary CI
# stays self-contained. Only the sync script's --check mode needs the sibling.
import json
from pathlib import Path
from typing import Any

import pytest
from unittest.mock import MagicMock, patch

import requests

from products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer import (
    BucketeerResumeConfig,
    bucketeer_source,
)
from products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.settings import (
    BUCKETEER_ENDPOINTS,
    CONTEXT_FIELD_BY_COLUMN,
)

FIXTURES = Path(__file__).parent / "fixtures"
BASE_URL = "https://bucketeer.example.com"
API_KEY = "secret-api-key-value"

IS_HOST_SAFE_PATCH = (
    "products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer._is_host_safe"
)
CLIENT_SESSION_PATCH = "products.warehouse_sources.backend.temporal.data_imports.sources.common.rest_source.rest_client.make_tracked_session"
CONTEXT_PATCH = (
    "products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer.fetch_export_context"
)


def fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text())


def http_response(body: dict[str, Any]) -> requests.Response:
    response = requests.Response()
    response.status_code = 200
    response.url = f"{BASE_URL}/v1/features"
    response.reason = "OK"
    response._content = json.dumps(body).encode()
    return response


def wire(session: MagicMock, responses: list[requests.Response]) -> list[dict[str, Any]]:
    session.headers = {}
    snapshots: list[dict[str, Any]] = []

    def _prepare(request: Any) -> MagicMock:
        snapshots.append(dict(request.params or {}))
        prepared = MagicMock()
        prepared.url = request.url
        return prepared

    session.prepare_request.side_effect = _prepare
    session.send.side_effect = responses
    return snapshots


def manager(resume: BucketeerResumeConfig | None = None) -> MagicMock:
    mock = MagicMock()
    mock.can_resume.return_value = resume is not None
    mock.load_state.return_value = resume
    return mock


def rows_of(source_response: Any) -> list[dict[str, Any]]:
    # SourceResponse.items is typed as sync-or-async; this source is always sync.
    return [row for page in source_response.items() for row in page]


def run_source(mgr: MagicMock, endpoint: str, responses: list[requests.Response]) -> tuple[list, list]:
    with (
        patch(IS_HOST_SAFE_PATCH, return_value=(True, None)),
        patch(CONTEXT_PATCH, return_value=fixture("context.json")),
        patch(CLIENT_SESSION_PATCH) as make_session,
    ):
        session = MagicMock()
        make_session.return_value = session
        params = wire(session, responses)
        source = bucketeer_source(
            instance_url=BASE_URL,
            api_key=API_KEY,
            endpoint=endpoint,
            team_id=1,
            job_id="j",
            resumable_source_manager=mgr,
        )
        rows = rows_of(source)
    return rows, params


class TestBucketeerContract:
    def test_fixtures_are_present(self) -> None:
        # A missing fixture means the sync script was never run for this checkout.
        assert (FIXTURES / "MANIFEST.json").is_file()
        for name in ("context.json", "feature_flags_page_1.json", "feature_flags_page_2.json"):
            assert (FIXTURES / name).is_file(), name

    def test_walks_both_feature_pages_from_the_canonical_fixtures(self) -> None:
        rows, params = run_source(
            manager(),
            "feature_flags",
            [http_response(fixture("feature_flags_page_1.json")), http_response(fixture("feature_flags_page_2.json"))],
        )

        assert [r["id"] for r in rows] == ["feature-alpha", "feature-beta"]
        # Page 2 is requested with the cursor page 1 returned.
        assert params[1]["cursor"] == fixture("feature_flags_page_1.json")["cursor"]

    def test_stops_on_the_empty_cursor_the_gateway_emits(self) -> None:
        # Bucketeer emits unpopulated fields, so the last page carries "" rather than
        # omitting the key. The source must treat that as the end.
        page_2 = fixture("feature_flags_page_2.json")
        assert page_2["cursor"] == ""
        rows, _ = run_source(manager(), "feature_flags", [http_response(page_2)])
        assert len(rows) == 1

    def test_resume_continues_without_losing_or_duplicating_a_row(self) -> None:
        # A sync interrupted after page 1 restarts from the saved cursor. Re-reading the
        # last page would be safe too, because merge dedupes on the composite key.
        rows, params = run_source(
            manager(BucketeerResumeConfig(cursor="1")),
            "feature_flags",
            [http_response(fixture("feature_flags_page_2.json"))],
        )
        assert params[0]["cursor"] == "1"
        assert [r["id"] for r in rows] == ["feature-beta"]

    @pytest.mark.parametrize(
        "endpoint,name,expected_id",
        [
            ("segments", "segments.json", "segment-early-access"),
            ("experiments", "experiments.json", "experiment-alpha"),
            ("goals", "goals.json", "goal-checkout-complete"),
            ("audit_logs", "audit_logs.json", "auditlog-0000000000"),
            ("code_references", "code_references.json", "coderef-0000000000"),
        ],
    )
    def test_each_table_parses_its_canonical_fixture(self, endpoint: str, name: str, expected_id: str) -> None:
        # A renamed selector or id field on the Bucketeer side surfaces here.
        rows, _ = run_source(manager(), endpoint, [http_response(fixture(name))])
        assert [r["id"] for r in rows] == [expected_id]

    def test_every_row_carries_the_authenticated_lineage(self) -> None:
        rows, _ = run_source(manager(), "feature_flags", [http_response(fixture("feature_flags_page_2.json"))])
        context = fixture("context.json")
        for column, key in CONTEXT_FIELD_BY_COLUMN.items():
            assert rows[0][column] == context[key], column

    def test_code_reference_cannot_claim_another_environment(self) -> None:
        # The fixture's record carries its own environmentId; the authenticated context
        # must win, or two environments could collide on the composite primary key.
        rows, _ = run_source(manager(), "code_references", [http_response(fixture("code_references.json"))])
        assert rows[0]["bucketeer_environment_id"] == fixture("context.json")["environmentId"]

    def test_composite_primary_key_on_every_table(self) -> None:
        for endpoint, config in BUCKETEER_ENDPOINTS.items():
            with patch(IS_HOST_SAFE_PATCH, return_value=(True, None)):
                source = bucketeer_source(
                    instance_url=BASE_URL,
                    api_key=API_KEY,
                    endpoint=endpoint,
                    team_id=1,
                    job_id="j",
                    resumable_source_manager=manager(),
                )
            assert source.primary_keys == ["bucketeer_environment_id", config.id_field], endpoint

    def test_capabilities_match_the_tables_this_source_implements(self) -> None:
        # Bucketeer advertises what a connector may read; syncing a table it does not
        # advertise would send the connector at an endpoint that may not exist.
        assert set(fixture("context.json")["capabilities"]) == set(BUCKETEER_ENDPOINTS)
