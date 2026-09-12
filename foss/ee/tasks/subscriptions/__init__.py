"""Subscription delivery (email, Slack, Teams) is an enterprise feature.

The subscriptions API is not registered in the FOSS build, so nothing schedules a delivery. These stubs
keep the export workflows importable and fail loudly if a delivery is ever attempted.
"""

from typing import Any

SLACK_USER_CONFIG_ERRORS: frozenset[str] = frozenset()


def _capture_delivery_failed_event(*args: Any, **kwargs: Any) -> None:
    return None
