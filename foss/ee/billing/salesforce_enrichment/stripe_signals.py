from dataclasses import dataclass
from typing import Any


@dataclass
class StripeSignals:
    items: dict[str, Any] | None = None


async def fetch_stripe_signals(*args: Any, **kwargs: Any) -> StripeSignals:
    return StripeSignals(items={})
