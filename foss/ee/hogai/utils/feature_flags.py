from typing import Any


def is_core_memory_disabled(*args: Any, **kwargs: Any) -> bool:
    """Core memory is part of PostHog AI; treat it as disabled so callers skip it."""
    return True
