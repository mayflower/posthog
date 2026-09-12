"""Building blocks for the FOSS shim: a clear error and factories for unavailable symbols."""

from collections.abc import Callable
from typing import Any


class EnterpriseFeatureUnavailable(RuntimeError):
    """Raised when code reaches an enterprise-only feature in the FOSS build."""

    def __init__(self, feature: str) -> None:
        super().__init__(f"{feature} is not available in the FOSS build of PostHog")
        self.feature = feature


class Unavailable:
    """Base class for enterprise classes the FOSS build cannot provide.

    Subclassing, generic subscripting and type annotations work at import time; instantiating raises.
    """

    foss_feature: str = "This enterprise feature"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise EnterpriseFeatureUnavailable(self.foss_feature)

    def __class_getitem__(cls, item: Any) -> type:
        return cls


def unavailable_class(name: str, feature: str, *bases: type) -> type:
    """Create a class that raises on instantiation but can be subclassed and subscripted."""
    return type(name, (*bases, Unavailable), {"foss_feature": feature, "__module__": "ee"})


def unavailable_function(name: str, feature: str) -> Callable[..., Any]:
    """Create a function that raises when called."""

    def _raise(*args: Any, **kwargs: Any) -> Any:
        raise EnterpriseFeatureUnavailable(feature)

    _raise.__name__ = name
    return _raise


def unavailable_async_function(name: str, feature: str) -> Callable[..., Any]:
    """Create a coroutine function that raises when awaited."""

    async def _raise(*args: Any, **kwargs: Any) -> Any:
        raise EnterpriseFeatureUnavailable(feature)

    _raise.__name__ = name
    return _raise
