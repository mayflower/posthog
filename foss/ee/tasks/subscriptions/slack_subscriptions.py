from dataclasses import dataclass, field
from typing import Any

from ee._foss import unavailable_async_function, unavailable_function

UTM_TAGS_BASE = "utm_source=posthog&utm_campaign=subscription_report"


@dataclass
class SlackMessage:
    text: str = ""
    blocks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SlackDeliveryResult:
    ok: bool = False
    error: str | None = None


def get_slack_integration_for_team(*args: Any, **kwargs: Any) -> None:
    return None


_prepare_slack_message = unavailable_function("_prepare_slack_message", "Slack subscription delivery")
deliver_slack_message_data = unavailable_function("deliver_slack_message_data", "Slack subscription delivery")
send_slack_message_with_integration_async = unavailable_async_function(
    "send_slack_message_with_integration_async", "Slack subscription delivery"
)
