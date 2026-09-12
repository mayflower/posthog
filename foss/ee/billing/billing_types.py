from enum import StrEnum
from typing import Any

BillingStatus = dict[str, Any]


class BillingProvider(StrEnum):
    STRIPE = "stripe"
    VERCEL = "vercel"
