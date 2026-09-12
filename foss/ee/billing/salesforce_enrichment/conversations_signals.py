from dataclasses import dataclass
from typing import Any


@dataclass
class ConversationsSlackSignals:
    items: dict[str, Any] | None = None


async def aggregate_conversations_slack_signals_for_orgs(
    *args: Any, **kwargs: Any
) -> dict[str, ConversationsSlackSignals]:
    return {}
