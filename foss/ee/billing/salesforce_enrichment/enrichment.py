from dataclasses import dataclass, field
from typing import Any

from ee._foss import unavailable_async_function, unavailable_function


@dataclass
class BulkUpdateResult:
    succeeded: int = 0
    failed: int = 0
    updated: int = 0
    errors: list[str] = field(default_factory=list)


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _extract_primary_tag(*args: Any, **kwargs: Any) -> str | None:
    return None


def _is_yc_funded(*args: Any, **kwargs: Any) -> bool:
    return False


bulk_update_salesforce_accounts = unavailable_function("bulk_update_salesforce_accounts", "Salesforce enrichment")
enrich_accounts_async = unavailable_async_function("enrich_accounts_async", "Salesforce enrichment")
