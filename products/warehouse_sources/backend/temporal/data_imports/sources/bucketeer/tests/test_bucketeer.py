import json
from typing import Any, Optional

import pytest
from unittest.mock import MagicMock, patch

import requests
from parameterized import parameterized

from products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer import (
    PAGE_SIZE,
    BucketeerHostNotAllowedError,
    BucketeerPaginationError,
    BucketeerResumeConfig,
    _headers,
    bucketeer_source,
    check_endpoint_permissions,
    normalize_instance_url,
    validate_credentials,
)
from products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.settings import CONTEXT_FIELD_BY_COLUMN

CLIENT_SESSION_PATCH = "products.warehouse_sources.backend.temporal.data_imports.sources.common.rest_source.rest_client.make_tracked_session"
IS_HOST_SAFE_PATCH = (
    "products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer._is_host_safe"
)
CONTEXT_PATCH = (
    "products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer.fetch_export_context"
)

BASE_URL = "https://bucketeer.example.com"
API_KEY = "secret-api-key-value"

EXPORT_CONTEXT = {
    "contractVersion": "1",
    "credentialScope": "environment",
    "organizationId": "org-1",
    "projectId": "prj-1",
    "projectUrlCode": "my-project",
    "environmentId": "env-1",
    "environmentName": "Production",
    "environmentUrlCode": "production",
    "capabilities": ["feature_flags", "segments", "experiments", "goals", "audit_logs", "code_references"],
}


def _json_response(body: Any, *, status_code: int = 200, location: Optional[str] = None) -> requests.Response:
    resp = requests.Response()
    resp.status_code = status_code
    resp.url = f"{BASE_URL}/v1/features"
    resp.reason = "OK" if status_code < 400 else "Error"
    if location is not None:
        resp.headers["Location"] = location
    resp._content = json.dumps(body).encode()
    return resp


def _mock_response(status_code: int = 200, json_data: Any = None, is_redirect: bool = False) -> MagicMock:
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.ok = status_code < 400
    response.is_redirect = is_redirect
    response.is_permanent_redirect = False
    response.json.return_value = json_data
    response.text = str(json_data)
    response.raise_for_status.side_effect = (
        requests.HTTPError(f"{status_code} Client Error", response=response) if status_code >= 400 else None
    )
    return response


def _make_manager(resume_state: BucketeerResumeConfig | None = None) -> MagicMock:
    manager = MagicMock()
    manager.can_resume.return_value = resume_state is not None
    manager.load_state.return_value = resume_state
    return manager


def _wire(session: MagicMock, responses: list[requests.Response]) -> list[dict[str, Any]]:
    """Wire a mock session, snapshotting each request's params at send time.

    ``request.params`` is one dict mutated in place across pages, so reading it after the run
    shows only the last page's state.
    """
    session.headers = {}
    param_snapshots: list[dict[str, Any]] = []

    def _prepare(request: Any) -> MagicMock:
        param_snapshots.append(dict(request.params or {}))
        prepared = MagicMock()
        prepared.url = request.url
        return prepared

    session.prepare_request.side_effect = _prepare
    session.send.side_effect = responses
    return param_snapshots


def _rows(source_response: Any) -> list[dict[str, Any]]:
    return [row for page in source_response.items() for row in page]


def _source(manager: MagicMock, endpoint: str = "feature_flags", instance_url: str = BASE_URL) -> Any:
    return bucketeer_source(
        instance_url=instance_url,
        api_key=API_KEY,
        endpoint=endpoint,
        team_id=1,
        job_id="j",
        resumable_source_manager=manager,
    )


class TestNormalizeAndHeaders:
    @parameterized.expand(
        [
            ("plain", "https://bucketeer.example.com", "https://bucketeer.example.com"),
            ("trailing_slash", "https://bucketeer.example.com/", "https://bucketeer.example.com"),
            ("v1_suffix", "https://bucketeer.example.com/v1", "https://bucketeer.example.com"),
            (
                "export_context_suffix",
                "https://bucketeer.example.com/v1/export/context",
                "https://bucketeer.example.com",
            ),
            ("no_scheme", "bucketeer.example.com", "https://bucketeer.example.com"),
            ("whitespace", "  https://bucketeer.example.com  ", "https://bucketeer.example.com"),
            (
                # A gateway behind a path prefix must keep the prefix.
                "path_prefix",
                "https://example.com/bucketeer/",
                "https://example.com/bucketeer",
            ),
        ]
    )
    def test_normalize_instance_url(self, _name: str, raw: str, expected: str) -> None:
        assert normalize_instance_url(raw) == expected

    def test_api_key_is_sent_raw_without_bearer_prefix(self) -> None:
        # Bucketeer reads the Authorization header verbatim; a Bearer prefix breaks auth.
        headers = _headers(API_KEY)
        assert headers["Authorization"] == API_KEY
        assert "Bearer" not in headers["Authorization"]


class TestValidateCredentials:
    def test_accepts_a_contract_v1_environment_key(self) -> None:
        with patch(
            "products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer._get_session"
        ) as session:
            session.return_value.get.return_value = _mock_response(200, EXPORT_CONTEXT)
            ok, err = validate_credentials(BASE_URL, API_KEY)
        assert (ok, err) == (True, None)

    @parameterized.expand(
        [
            ("unauthorized", 401, "Invalid Bucketeer API key"),
            ("forbidden", 403, "public API read role"),
            ("not_found", 404, "analytics export contract"),
        ]
    )
    def test_maps_status_to_a_useful_message(self, _name: str, status: int, expected_fragment: str) -> None:
        with patch(
            "products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer._get_session"
        ) as session:
            session.return_value.get.return_value = _mock_response(status, None)
            ok, err = validate_credentials(BASE_URL, API_KEY)
        assert ok is False
        assert err is not None and expected_fragment in err

    def test_rejects_an_unsupported_contract_version(self) -> None:
        with patch(
            "products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer._get_session"
        ) as session:
            session.return_value.get.return_value = _mock_response(200, {**EXPORT_CONTEXT, "contractVersion": "2"})
            ok, err = validate_credentials(BASE_URL, API_KEY)
        assert ok is False
        assert err is not None and "version 2" in err

    def test_rejects_a_non_environment_credential_scope(self) -> None:
        # The core connector reads one environment per connection; an org-scoped key needs the
        # multi-environment fan-out, so accepting it here would silently sync only one.
        with patch(
            "products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer._get_session"
        ) as session:
            session.return_value.get.return_value = _mock_response(
                200, {**EXPORT_CONTEXT, "credentialScope": "organization"}
            )
            ok, err = validate_credentials(BASE_URL, API_KEY)
        assert ok is False
        assert err is not None and "environment-scoped" in err

    def test_rejects_context_missing_required_fields(self) -> None:
        partial = {k: v for k, v in EXPORT_CONTEXT.items() if k != "environmentId"}
        with patch(
            "products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer._get_session"
        ) as session:
            session.return_value.get.return_value = _mock_response(200, partial)
            ok, err = validate_credentials(BASE_URL, API_KEY)
        assert ok is False
        assert err is not None and "missing required environment fields" in err

    def test_refuses_a_redirect(self) -> None:
        # A validated host could 3xx to an internal address, defeating the host check.
        with patch(
            "products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer._get_session"
        ) as session:
            session.return_value.get.return_value = _mock_response(302, None, is_redirect=True)
            ok, err = validate_credentials(BASE_URL, API_KEY)
        assert ok is False
        assert err is not None and "not allowed" in err

    @parameterized.expand(
        [
            ("userinfo", "https://user@evil.example.com"),
            ("backslash_parser_differential", "https://127.0.0.1\\@example.com"),
            ("non_http_scheme", "ftp://bucketeer.example.com"),
        ]
    )
    def test_rejects_an_unsafe_url(self, _name: str, url: str) -> None:
        ok, err = validate_credentials(url, API_KEY)
        assert ok is False
        assert err == "Invalid Bucketeer instance URL"

    def test_blocks_a_host_that_resolves_internally(self) -> None:
        with patch(IS_HOST_SAFE_PATCH, return_value=(False, "Host not allowed")):
            ok, err = validate_credentials(BASE_URL, API_KEY, team_id=1)
        assert ok is False
        assert err == "Host not allowed"


class TestEndpointPermissions:
    def test_reports_denials_but_not_transient_failures(self) -> None:
        with (
            patch(IS_HOST_SAFE_PATCH, return_value=(True, None)),
            patch(
                "products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.bucketeer._get_session"
            ) as session,
        ):
            session.return_value.get.side_effect = [
                _mock_response(200, {"features": []}),
                _mock_response(403, {"message": "not authorized"}),
                _mock_response(401, None),
                _mock_response(429, None),
                _mock_response(500, None),
                requests.exceptions.ConnectionError("boom"),
            ]
            result = check_endpoint_permissions(
                BASE_URL,
                API_KEY,
                ["feature_flags", "segments", "experiments", "goals", "audit_logs", "code_references"],
                team_id=1,
            )
        assert result["feature_flags"] is None
        assert result["segments"] == "not authorized"
        assert result["experiments"] == "Invalid Bucketeer API key"
        # 429/5xx/network are not evidence a table is forbidden.
        assert result["goals"] is None
        assert result["audit_logs"] is None
        assert result["code_references"] is None


class TestPagination:
    def test_walks_three_pages_and_stops_on_an_empty_cursor(self) -> None:
        manager = _make_manager()
        with (
            patch(IS_HOST_SAFE_PATCH, return_value=(True, None)),
            patch(CONTEXT_PATCH, return_value=EXPORT_CONTEXT),
            patch(CLIENT_SESSION_PATCH) as make_session,
        ):
            session = MagicMock()
            make_session.return_value = session
            params = _wire(
                session,
                [
                    _json_response({"features": [{"id": "f1"}], "cursor": "1", "totalCount": 3}),
                    _json_response({"features": [{"id": "f2"}], "cursor": "2", "totalCount": 3}),
                    # EmitUnpopulated means the exhausted cursor is "" rather than absent.
                    _json_response({"features": [{"id": "f3"}], "cursor": "", "totalCount": 3}),
                ],
            )
            rows = _rows(_source(manager))

        assert [r["id"] for r in rows] == ["f1", "f2", "f3"]
        assert params[0]["pageSize"] == PAGE_SIZE
        assert params[1]["cursor"] == "1"
        assert params[2]["cursor"] == "2"

    def test_stops_when_the_cursor_key_is_absent_entirely(self) -> None:
        manager = _make_manager()
        with (
            patch(IS_HOST_SAFE_PATCH, return_value=(True, None)),
            patch(CONTEXT_PATCH, return_value=EXPORT_CONTEXT),
            patch(CLIENT_SESSION_PATCH) as make_session,
        ):
            session = MagicMock()
            make_session.return_value = session
            _wire(session, [_json_response({"features": [{"id": "f1"}]})])
            rows = _rows(_source(manager))
        assert [r["id"] for r in rows] == ["f1"]

    def test_raises_when_the_server_repeats_a_cursor(self) -> None:
        # A repeated cursor means pagination is not advancing; walking it would never end.
        manager = _make_manager()
        with (
            patch(IS_HOST_SAFE_PATCH, return_value=(True, None)),
            patch(CONTEXT_PATCH, return_value=EXPORT_CONTEXT),
            patch(CLIENT_SESSION_PATCH) as make_session,
        ):
            session = MagicMock()
            make_session.return_value = session
            _wire(
                session,
                [
                    _json_response({"features": [{"id": "f1"}], "cursor": "same"}),
                    _json_response({"features": [{"id": "f2"}], "cursor": "same"}),
                ],
            )
            with pytest.raises(BucketeerPaginationError):
                _rows(_source(manager))

    def test_empty_page_yields_nothing(self) -> None:
        manager = _make_manager()
        with (
            patch(IS_HOST_SAFE_PATCH, return_value=(True, None)),
            patch(CONTEXT_PATCH, return_value=EXPORT_CONTEXT),
            patch(CLIENT_SESSION_PATCH) as make_session,
        ):
            session = MagicMock()
            make_session.return_value = session
            _wire(session, [_json_response({"features": [], "cursor": ""})])
            assert _rows(_source(manager)) == []


class TestResume:
    def test_saves_state_only_after_a_page_is_yielded(self) -> None:
        manager = _make_manager()
        with (
            patch(IS_HOST_SAFE_PATCH, return_value=(True, None)),
            patch(CONTEXT_PATCH, return_value=EXPORT_CONTEXT),
            patch(CLIENT_SESSION_PATCH) as make_session,
        ):
            session = MagicMock()
            make_session.return_value = session
            _wire(
                session,
                [
                    _json_response({"features": [{"id": "f1"}], "cursor": "1"}),
                    _json_response({"features": [{"id": "f2"}], "cursor": ""}),
                ],
            )
            _rows(_source(manager))

        saved = [c.args[0].cursor for c in manager.save_state.call_args_list]
        # Only the cursor pointing at a remaining page is checkpointed.
        assert saved == ["1"]

    def test_resumes_from_the_saved_cursor(self) -> None:
        manager = _make_manager(BucketeerResumeConfig(cursor="5"))
        with (
            patch(IS_HOST_SAFE_PATCH, return_value=(True, None)),
            patch(CONTEXT_PATCH, return_value=EXPORT_CONTEXT),
            patch(CLIENT_SESSION_PATCH) as make_session,
        ):
            session = MagicMock()
            make_session.return_value = session
            params = _wire(session, [_json_response({"features": [{"id": "f6"}], "cursor": ""})])
            rows = _rows(_source(manager))

        assert params[0]["cursor"] == "5"
        assert [r["id"] for r in rows] == ["f6"]

    def test_a_resumed_run_keeps_walking_forward(self) -> None:
        manager = _make_manager(BucketeerResumeConfig(cursor="5"))
        with (
            patch(IS_HOST_SAFE_PATCH, return_value=(True, None)),
            patch(CONTEXT_PATCH, return_value=EXPORT_CONTEXT),
            patch(CLIENT_SESSION_PATCH) as make_session,
        ):
            session = MagicMock()
            make_session.return_value = session
            params = _wire(
                session,
                [
                    _json_response({"features": [{"id": "f6"}], "cursor": "6"}),
                    _json_response({"features": [{"id": "f7"}], "cursor": ""}),
                ],
            )
            rows = _rows(_source(manager))

        assert [r["id"] for r in rows] == ["f6", "f7"]
        assert params[0]["cursor"] == "5"
        assert params[1]["cursor"] == "6"

    def test_a_resumed_run_fails_fast_if_the_server_echoes_the_seeded_cursor(self) -> None:
        # Seeding the resume cursor into the seen set means a server that hands it straight
        # back is caught on the first response, instead of costing another duplicate page.
        manager = _make_manager(BucketeerResumeConfig(cursor="5"))
        with (
            patch(IS_HOST_SAFE_PATCH, return_value=(True, None)),
            patch(CONTEXT_PATCH, return_value=EXPORT_CONTEXT),
            patch(CLIENT_SESSION_PATCH) as make_session,
        ):
            session = MagicMock()
            make_session.return_value = session
            _wire(session, [_json_response({"features": [{"id": "f6"}], "cursor": "5"})])
            with pytest.raises(BucketeerPaginationError):
                _rows(_source(manager))


class TestEnvironmentContext:
    def test_every_row_carries_the_authenticated_lineage(self) -> None:
        manager = _make_manager()
        with (
            patch(IS_HOST_SAFE_PATCH, return_value=(True, None)),
            patch(CONTEXT_PATCH, return_value=EXPORT_CONTEXT),
            patch(CLIENT_SESSION_PATCH) as make_session,
        ):
            session = MagicMock()
            make_session.return_value = session
            _wire(session, [_json_response({"features": [{"id": "f1"}], "cursor": ""})])
            rows = _rows(_source(manager))

        row = rows[0]
        for column in CONTEXT_FIELD_BY_COLUMN:
            assert column in row
        assert row["bucketeer_environment_id"] == "env-1"
        assert row["bucketeer_organization_id"] == "org-1"
        assert row["bucketeer_contract_version"] == "1"

    def test_a_payload_cannot_spoof_the_environment(self) -> None:
        # code_references carries its own environmentId; the authenticated context must win,
        # otherwise a record could attribute itself to another environment and collide on the
        # composite primary key.
        manager = _make_manager()
        with (
            patch(IS_HOST_SAFE_PATCH, return_value=(True, None)),
            patch(CONTEXT_PATCH, return_value=EXPORT_CONTEXT),
            patch(CLIENT_SESSION_PATCH) as make_session,
        ):
            session = MagicMock()
            make_session.return_value = session
            _wire(
                session,
                [
                    _json_response(
                        {
                            "codeReferences": [
                                {
                                    "id": "c1",
                                    "environmentId": "someone-elses-env",
                                    "bucketeer_environment_id": "spoofed",
                                }
                            ],
                            "cursor": "",
                        }
                    )
                ],
            )
            rows = _rows(_source(manager, endpoint="code_references"))

        assert rows[0]["bucketeer_environment_id"] == "env-1"
        # The record's own field is preserved, but it is not the lineage column.
        assert rows[0]["environmentId"] == "someone-elses-env"

    def test_primary_key_is_composite(self) -> None:
        manager = _make_manager()
        response = _source(manager)
        assert response.primary_keys == ["bucketeer_environment_id", "id"]


class TestHostSafetyAtRunTime:
    def test_a_host_that_became_unsafe_stops_the_sync(self) -> None:
        # Re-checked at run time, not just at source-create: the URL may have been edited or
        # may now resolve to an internal address (DNS rebinding).
        manager = _make_manager()
        with patch(IS_HOST_SAFE_PATCH, return_value=(False, "Host not allowed")):
            with pytest.raises(BucketeerHostNotAllowedError):
                _rows(_source(manager))
