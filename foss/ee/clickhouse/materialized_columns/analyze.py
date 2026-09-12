from typing import Any


def materialize_properties_task(*args: Any, **kwargs: Any) -> None:
    """Scheduled by Celery beat; a no-op keeps the beat schedule healthy."""
    return None
