"""Billing talks to the PostHog Cloud billing service, which a self-hosted FOSS instance does not have.

Core only reaches these on Cloud paths (``is_cloud()`` plus a license), so the class exists for imports and
raises if something calls it anyway.
"""

from enum import StrEnum
from typing import Any

from ee._foss import EnterpriseFeatureUnavailable


class BillingServiceOpenInvoicesError(Exception):
    pass


class FundingStatusUnavailable(Exception):
    pass


class PrepaidCreditState(StrEnum):
    NONE = "none"


class StartupProgramLabel(StrEnum):
    NONE = "none"


class OrganizationFundingStatus:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise EnterpriseFeatureUnavailable("Billing")


class BillingManager:
    def __init__(self, license: Any = None, user: Any = None, *args: Any, **kwargs: Any) -> None:
        self.license = license
        self.user = user

    def __getattr__(self, name: str) -> Any:
        raise EnterpriseFeatureUnavailable("Billing")


def build_billing_token(*args: Any, **kwargs: Any) -> str:
    raise EnterpriseFeatureUnavailable("Billing")
