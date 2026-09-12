from dataclasses import dataclass
from typing import Any

from ee._foss import EnterpriseFeatureUnavailable, unavailable_class, unavailable_function

tables: dict[str, Any] = {}


@dataclass(frozen=True)
class MaterializedColumnDetails:
    table_column: str
    property_name: str
    is_disabled: bool = False


MaterializedColumn = unavailable_class("MaterializedColumn", "Materialized columns")
MinMaxIndex = unavailable_class("MinMaxIndex", "Materialized column indexes")
BloomFilterIndex = unavailable_class("BloomFilterIndex", "Materialized column indexes")
BloomFilterLowerIndex = unavailable_class("BloomFilterLowerIndex", "Materialized column indexes")
NgramLowerIndex = unavailable_class("NgramLowerIndex", "Materialized column indexes")


def get_materialized_columns(*args: Any, **kwargs: Any) -> dict[Any, Any]:
    return {}


def get_enabled_materialized_columns(*args: Any, **kwargs: Any) -> dict[Any, Any]:
    return {}


def get_bloom_filter_lower_index_name(*args: Any, **kwargs: Any) -> str:
    raise EnterpriseFeatureUnavailable("Materialized column indexes")


def check_index_exists(*args: Any, **kwargs: Any) -> bool:
    return False


materialize = unavailable_function("materialize", "Materialized columns")
backfill_materialized_columns = unavailable_function("backfill_materialized_columns", "Materialized columns")
drop_column = unavailable_function("drop_column", "Materialized columns")
