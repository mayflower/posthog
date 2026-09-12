"""SCIM helpers used by the core organization-domain and identity-provider APIs."""

from typing import Any

from ee._foss import EnterpriseFeatureUnavailable


def get_scim_base_url(*args: Any, **kwargs: Any) -> str | None:
    return None


def mask_email(value: str) -> str:
    local, _, domain = value.partition("@")
    if not domain:
        return mask_string(value)
    return f"{local[:1]}***@{domain}"


def mask_string(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


def enable_scim_for_config(*args: Any, **kwargs: Any) -> None:
    raise EnterpriseFeatureUnavailable("SCIM provisioning")


def disable_scim_for_config(*args: Any, **kwargs: Any) -> None:
    raise EnterpriseFeatureUnavailable("SCIM provisioning")


def regenerate_scim_token_for_config(*args: Any, **kwargs: Any) -> None:
    raise EnterpriseFeatureUnavailable("SCIM provisioning")
