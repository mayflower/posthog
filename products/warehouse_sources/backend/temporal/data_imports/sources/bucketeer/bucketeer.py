import re
import dataclasses
from collections.abc import Iterator
from typing import Any, Optional
from urllib.parse import urlparse

import requests
from requests import Request, Response

from posthog.cloud_utils import is_cloud

from products.warehouse_sources.backend.temporal.data_imports.sources.bucketeer.settings import (
    BUCKETEER_ENDPOINTS,
    CONTEXT_FIELD_BY_COLUMN,
    EXPORT_CONTEXT_PATH,
    SUPPORTED_CONTRACT_VERSION,
    SUPPORTED_CREDENTIAL_SCOPE,
)
from products.warehouse_sources.backend.temporal.data_imports.sources.common.http import make_tracked_session
from products.warehouse_sources.backend.temporal.data_imports.sources.common.mixins import _is_host_safe
from products.warehouse_sources.backend.temporal.data_imports.sources.common.rest_source import (
    Endpoint,
    RESTAPIConfig,
    rest_api_resource,
)
from products.warehouse_sources.backend.temporal.data_imports.sources.common.rest_source.paginators import (
    JSONResponseCursorPaginator,
)
from products.warehouse_sources.backend.temporal.data_imports.sources.common.resumable import ResumableSourceManager
from products.warehouse_sources.backend.temporal.data_imports.sources.common.typings import SourceResponse

# Bucketeer caps audit_logs at 200 per page and accepts the same parameter everywhere.
PAGE_SIZE = 100

# (connect, read) seconds for every sync request. The instance is customer-controlled and
# self-hosted, so a gateway that accepts a connection and then never responds would hold an
# import worker for the whole activity timeout.
REQUEST_TIMEOUT_SECONDS = (10.0, 60.0)

HOST_NOT_ALLOWED_ERROR = "Bucketeer instance URL is not allowed"


class BucketeerHostNotAllowedError(Exception):
    pass


class BucketeerPaginationError(Exception):
    pass


@dataclasses.dataclass
class BucketeerResumeConfig:
    # Cursor of the next page to fetch. Saved only after the corresponding page has been
    # yielded, so a crash re-yields the last page (merge dedupes on the composite primary
    # key) rather than skipping it.
    cursor: Optional[str] = None


class BucketeerCursorPaginator(JSONResponseCursorPaginator):
    """Cursor paginator that refuses to walk a cursor the server already gave us.

    The shared paginator models Bucketeer's envelope correctly, including the empty-cursor
    stop: the gateway serializes with EmitUnpopulated, so an exhausted walk arrives as
    ``"cursor": ""`` rather than a missing key, and an empty string is falsy. What it does
    not do is notice a server that keeps handing back the same cursor. That would spin
    forever against a paginated endpoint, so fail the sync instead.
    """

    def __init__(self) -> None:
        super().__init__(cursor_path="cursor", cursor_param="cursor")
        self._seen_cursors: set[str] = set()

    def update_state(self, response: Response, data: Optional[list[Any]] = None) -> None:
        super().update_state(response, data)
        if not self._has_next_page or self._cursor_value is None:
            return
        if self._cursor_value in self._seen_cursors:
            raise BucketeerPaginationError(
                "Bucketeer returned a cursor it had already returned, so pagination is not "
                "advancing. Stopping to avoid an endless sync."
            )
        self._seen_cursors.add(self._cursor_value)

    def init_request(self, request: Request) -> None:
        super().init_request(request)
        # A resumed run starts from a saved cursor, which must not later count as a repeat.
        if self._cursor_value is not None:
            self._seen_cursors.add(self._cursor_value)


def normalize_instance_url(instance_url: str) -> str:
    """Turn whatever the user typed into a consistent instance base URL.

    A Bucketeer gateway may sit behind a path prefix, so the path is preserved. Only a
    scheme-less prefix, trailing slashes, and an accidentally pasted API suffix are stripped,
    and only when stripping is unambiguous.
    """
    url = instance_url.strip().rstrip("/")
    # Only default the scheme for bare hosts — a non-http(s) scheme must survive so
    # _validated_hostname can reject it.
    if url and "://" not in url:
        url = f"https://{url}"
    for suffix in (EXPORT_CONTEXT_PATH, "/v1"):
        if url.lower().endswith(suffix):
            url = url[: -len(suffix)]
            break
    return url.rstrip("/")


def _headers(api_key: str) -> dict[str, str]:
    # Bucketeer reads the public API key as the raw Authorization header value, with no
    # Bearer prefix (pkg/api/api/api.go reads the header verbatim).
    return {"Authorization": api_key, "Accept": "application/json"}


def _get_session(api_key: str) -> requests.Session:
    # The instance URL is user-supplied, so pin redirects off to keep host validation and the
    # outbound request on the same target (SSRF defense-in-depth), and redact the key.
    return make_tracked_session(headers=_headers(api_key), redact_values=(api_key,), allow_redirects=False)


def _validated_hostname(base_url: str) -> Optional[str]:
    """Hostname of the normalized instance URL, or None when malformed or ambiguous.

    SSRF guard: urlparse treats a backslash as ordinary userinfo and "@" as a userinfo
    separator, but urllib3/requests treat the backslash as an authority separator, so
    ``https://127.0.0.1\\@example.com`` validates as example.com yet connects to 127.0.0.1.
    A legitimate instance URL has no userinfo, so reject either construct outright.
    """
    if "\\" in base_url or "%5c" in base_url.lower():
        return None
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https") or "@" in parsed.netloc:
        return None
    # The API key rides in the Authorization header on every request, so plaintext http would
    # leak it to any network observer. On PostHog Cloud the request egresses over the public
    # internet, so require https. Self-hosted operators control their own network path, so
    # http stays allowed there — mirroring how host IP safety is only enforced on cloud.
    if parsed.scheme == "http" and is_cloud():
        return None
    hostname = parsed.hostname
    if not hostname or not re.match(r"^[A-Za-z0-9.\-]+$", hostname):
        return None
    return hostname


def _resolved_base_url(instance_url: str, team_id: Optional[int]) -> tuple[Optional[str], Optional[str]]:
    """The normalized base URL to talk to, or the reason it is not safe to.

    The instance URL is fully customer-controlled, so a host that resolves to a private or
    internal address is refused (SSRF). Host safety is only enforced on cloud, and only
    when a team is known — see _is_host_safe.
    """
    base_url = normalize_instance_url(instance_url)
    hostname = _validated_hostname(base_url)
    if not hostname:
        return None, "Invalid Bucketeer instance URL"
    if team_id is not None:
        host_ok, host_err = _is_host_safe(hostname, team_id)
        if not host_ok:
            return None, host_err or HOST_NOT_ALLOWED_ERROR
    return base_url, None


def _check_host(instance_url: str, team_id: int) -> None:
    hostname = _validated_hostname(normalize_instance_url(instance_url))
    if not hostname:
        raise BucketeerHostNotAllowedError(HOST_NOT_ALLOWED_ERROR)
    host_ok, host_err = _is_host_safe(hostname, team_id)
    if not host_ok:
        raise BucketeerHostNotAllowedError(host_err or HOST_NOT_ALLOWED_ERROR)


def _error_message(response: requests.Response) -> Optional[str]:
    """Human-readable message from a Bucketeer error body, if it has one.

    Only the `message` string is read. The rest of the body is not surfaced, because an error
    payload echoed back to the user could carry request details.
    """
    try:
        body = response.json()
        if isinstance(body, dict) and isinstance(body.get("message"), str):
            return body["message"]
    except Exception:
        pass
    return None


def fetch_export_context(base_url: str, api_key: str) -> dict[str, Any]:
    """Read GET /v1/export/context, the authenticated lineage for every row of this run."""
    session = _get_session(api_key)
    response = session.get(f"{base_url}{EXPORT_CONTEXT_PATH}", timeout=15)
    if response.is_redirect or response.is_permanent_redirect:
        raise BucketeerHostNotAllowedError(HOST_NOT_ALLOWED_ERROR)
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise ValueError("Bucketeer export context response was not an object")
    # Re-checked every run, not just at connect: a server upgraded in between could stop
    # emitting a field, and a missing environment id would leave half the composite primary
    # key null on every row.
    missing = [key for key in CONTEXT_FIELD_BY_COLUMN.values() if not body.get(key)]
    if missing:
        raise ValueError(f"Bucketeer export context is missing required fields: {', '.join(sorted(missing))}")
    return body


def _context_columns(context: dict[str, Any]) -> dict[str, Any]:
    return {column: context.get(key) for column, key in CONTEXT_FIELD_BY_COLUMN.items()}


def bucketeer_source(
    instance_url: str,
    api_key: str,
    endpoint: str,
    team_id: int,
    job_id: str,
    resumable_source_manager: ResumableSourceManager[BucketeerResumeConfig],
) -> SourceResponse:
    config = BUCKETEER_ENDPOINTS[endpoint]
    base_url = normalize_instance_url(instance_url)

    endpoint_config: Endpoint = {
        "path": config.path,
        "data_selector": config.data_selector,
        # A 200 whose body is not the expected list shape is treated as a transient upstream
        # glitch and retried, rather than silently yielding nothing.
        "data_selector_malformed_retryable": True,
        "params": {"pageSize": PAGE_SIZE},
    }

    paginator = BucketeerCursorPaginator()

    rest_config: RESTAPIConfig = {
        "client": {
            "base_url": base_url,
            # Auth is supplied through the framework auth config so the key is redacted from
            # logs and raised errors; only the non-secret Accept header is set here.
            "headers": {"Accept": "application/json"},
            "auth": {"type": "api_key", "api_key": api_key, "name": "Authorization", "location": "header"},
            "paginator": paginator,
            # The instance URL is user-supplied: pin every request (including pagination) to
            # the base host and refuse redirects so a credentialed request cannot be bounced
            # off-host.
            "allowed_hosts": [],
            "allow_redirects": False,
            "request_timeout": REQUEST_TIMEOUT_SECONDS,
        },
        "resource_defaults": {},
        "resources": [
            {
                "name": endpoint,
                "endpoint": endpoint_config,
            }
        ],
    }

    initial_paginator_state: Optional[dict[str, Any]] = None
    if resumable_source_manager.can_resume():
        resume = resumable_source_manager.load_state()
        if resume is not None and resume.cursor:
            initial_paginator_state = {"cursor": resume.cursor}

    def save_checkpoint(state: Optional[dict[str, Any]]) -> None:
        # Persist only when a next page remains, and only after the current page was yielded.
        if state and state.get("cursor"):
            resumable_source_manager.save_state(BucketeerResumeConfig(cursor=str(state["cursor"])))

    def items() -> Iterator[list[dict[str, Any]]]:
        # Re-check at run time (not just at source-create) in case the instance URL was edited
        # or now resolves to an internal address (SSRF / DNS rebinding).
        _check_host(instance_url, team_id)

        # Fetched once per run: every row carries the environment the key is bound to, so a
        # resource payload cannot claim a different environment than the caller authenticated
        # as.
        context = _context_columns(fetch_export_context(base_url, api_key))

        resource = rest_api_resource(
            rest_config,
            team_id,
            job_id,
            None,
            resume_hook=save_checkpoint,
            initial_paginator_state=initial_paginator_state,
        )
        for batch in resource:
            if not batch:
                continue
            yield [{**row, **context} for row in batch]

        # The walk finished, so drop the checkpoint. Left in place, a later attempt within
        # the same job would resume at the final page's cursor and yield only those rows —
        # and because every table is full refresh, that page would replace the whole table.
        resumable_source_manager.clear_state()

    return SourceResponse(
        name=endpoint,
        items=items,
        primary_keys=["bucketeer_environment_id", config.id_field],
        partition_count=1,
        partition_size=1,
    )


def validate_credentials(
    instance_url: str, api_key: str, schema_name: Optional[str] = None, team_id: Optional[int] = None
) -> tuple[bool, str | None]:
    """Confirm the key is genuine and the server speaks a contract version we understand."""
    base_url, host_error = _resolved_base_url(instance_url, team_id)
    if base_url is None:
        return False, host_error

    session = _get_session(api_key)
    try:
        # The session never follows redirects: the validated host could 3xx to an internal
        # address, defeating the host check above.
        response = session.get(f"{base_url}{EXPORT_CONTEXT_PATH}", timeout=15)
    except requests.exceptions.RequestException as e:
        return False, f"Could not connect to Bucketeer: {e}"

    if response.is_redirect or response.is_permanent_redirect:
        return False, HOST_NOT_ALLOWED_ERROR

    if response.status_code == 401:
        return False, "Invalid Bucketeer API key"

    if response.status_code == 403:
        return False, (_error_message(response) or "Your Bucketeer API key does not have a public API read role")

    if response.status_code == 404:
        return False, (
            "This Bucketeer server does not expose the analytics export contract. It needs a "
            "version that serves GET /v1/export/context."
        )

    if response.status_code != 200:
        return False, _error_message(response) or f"Bucketeer returned HTTP {response.status_code}"

    try:
        context = response.json()
    except Exception:
        return False, "Bucketeer returned an unreadable export context response"

    if not isinstance(context, dict):
        return False, "Bucketeer returned an unreadable export context response"

    version = context.get("contractVersion")
    if version != SUPPORTED_CONTRACT_VERSION:
        return False, (
            f"This Bucketeer server speaks export contract version {version or 'unknown'}, "
            f"but this connector supports version {SUPPORTED_CONTRACT_VERSION}."
        )

    scope = context.get("credentialScope")
    if scope != SUPPORTED_CREDENTIAL_SCOPE:
        return False, (
            f"This connector needs an environment-scoped Bucketeer API key, but the key "
            f"presented is scoped to '{scope or 'unknown'}'."
        )

    missing = [key for key in CONTEXT_FIELD_BY_COLUMN.values() if not context.get(key)]
    if missing:
        return False, "Bucketeer export context is missing required environment fields"

    return True, None


def check_endpoint_permissions(
    instance_url: str, api_key: str, endpoints: list[str], team_id: int
) -> dict[str, str | None]:
    """Probe each endpoint and report which ones the key cannot read.

    Returns ``{endpoint: None}`` when reachable and ``{endpoint: reason}`` on a real denial
    (401/403). Throttles, 5xx and network blips are not permission problems, so they report as
    reachable rather than blocking the schema picker on a transient failure.
    """
    base_url, host_error = _resolved_base_url(instance_url, team_id)
    if base_url is None:
        return dict.fromkeys(endpoints, host_error)

    session = _get_session(api_key)
    results: dict[str, str | None] = {}
    for endpoint in endpoints:
        config = BUCKETEER_ENDPOINTS.get(endpoint)
        if config is None:
            results[endpoint] = None
            continue
        try:
            response = session.get(f"{base_url}{config.path}", params={"pageSize": 1}, timeout=15)
        except requests.exceptions.RequestException:
            results[endpoint] = None
            continue
        if response.status_code == 401:
            results[endpoint] = "Invalid Bucketeer API key"
        elif response.status_code == 403:
            results[endpoint] = (
                _error_message(response) or "Your Bucketeer API key does not have permission to read this table"
            )
        elif response.status_code == 404:
            # Not a permission problem: this deployment does not serve the endpoint at all.
            # Reporting it here greys the table out instead of failing a sync later.
            results[endpoint] = "This Bucketeer deployment does not expose this table"
        else:
            results[endpoint] = None
    return results
