"""Listed in ``CELERY_IMPORTS`` by core settings, so the worker needs the module to exist."""

from typing import Any

from celery import shared_task


@shared_task(ignore_result=True)
def refresh_org_self_driving_quota_task(*args: Any, **kwargs: Any) -> None:
    """Self-driving quotas come from PostHog Cloud billing; nothing to refresh in the FOSS build."""
    return None
