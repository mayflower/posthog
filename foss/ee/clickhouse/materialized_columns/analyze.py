from typing import Any

from ee._foss import unavailable_function


def materialize_properties_task(*args: Any, **kwargs: Any) -> None:
    """Scheduled by Celery beat; a no-op keeps the beat schedule healthy."""
    return None


materialize = unavailable_function("materialize", "Materialized columns")
