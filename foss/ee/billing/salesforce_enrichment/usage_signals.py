from dataclasses import dataclass
from typing import Any


@dataclass
class UsageSignals:
    items: dict[str, Any] | None = None


async def aggregate_usage_signals_for_orgs(*args: Any, **kwargs: Any) -> dict[str, UsageSignals]:
    return {}
