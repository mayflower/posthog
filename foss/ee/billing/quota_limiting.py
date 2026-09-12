"""Quota limiting is driven by PostHog Cloud billing. The FOSS build never limits anything.

``update_all_orgs_billing_quotas`` is intentionally not defined: the Temporal workflow that calls it
catches ``ImportError`` and skips the run.
"""

from collections.abc import Iterable
from enum import StrEnum
from typing import Any

from posthog.redis import get_client as _get_redis_client


class QuotaResource(StrEnum):
    EVENTS = "events"
    EXCEPTIONS = "exceptions"
    RECORDINGS = "recordings"
    ROWS_SYNCED = "rows_synced"
    ROWS_EXPORTED = "rows_exported"
    FEATURE_FLAG_REQUESTS = "feature_flag_requests"
    API_QUERIES = "api_queries_read_bytes"
    LLM_EVENTS = "llm_events"
    AI_CREDITS = "ai_credits"
    SIGNALS_CREDITS = "signals_credits"
    REPLAY_VISION_CREDITS = "replay_vision_credits"
    POSTHOG_CODE_CREDITS = "posthog_code_credits"


class QuotaLimitingCaches(StrEnum):
    QUOTA_LIMITER_CACHE_KEY = "@posthog/quota-limits/"
    QUOTA_LIMITING_SUSPENDED_KEY = "@posthog/quota-limiting-suspended/"


def get_client(*args: Any, **kwargs: Any) -> Any:
    return _get_redis_client(*args, **kwargs)


def is_team_limited(*args: Any, **kwargs: Any) -> bool:
    return False


def is_team_over_ai_credit_budget(*args: Any, **kwargs: Any) -> bool:
    return False


def list_limited_team_attributes(*args: Any, **kwargs: Any) -> list[str]:
    return []


def add_limited_team_tokens(*args: Any, **kwargs: Any) -> None:
    return None


def remove_limited_team_tokens(*args: Any, **kwargs: Any) -> None:
    return None


def update_organization_usage_fields(*args: Any, **kwargs: Any) -> None:
    return None


def dispatch_recordings_remote_config_sync(team_ids: Iterable[int], *args: Any, **kwargs: Any) -> None:
    return None


def invalidate_llm_gateway_quota_cache(*args: Any, **kwargs: Any) -> None:
    return None
