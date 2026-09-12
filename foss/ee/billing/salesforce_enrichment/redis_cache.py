from typing import Any


class OrgMappingsCacheMissingError(Exception):
    pass


async def get_cached_accounts_count(*args: Any, **kwargs: Any) -> int:
    return 0


async def get_cached_org_mappings_count(*args: Any, **kwargs: Any) -> int:
    return 0


async def get_org_mappings_page(*args: Any, **kwargs: Any) -> list[Any]:
    return []


async def get_stripe_enrichment_watermark(*args: Any, **kwargs: Any) -> None:
    return None


async def set_stripe_enrichment_watermark(*args: Any, **kwargs: Any) -> None:
    return None


async def store_accounts_in_redis(*args: Any, **kwargs: Any) -> None:
    return None


async def store_org_mappings_in_redis(*args: Any, **kwargs: Any) -> None:
    return None
