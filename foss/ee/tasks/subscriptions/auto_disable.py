from enum import StrEnum
from typing import Any


class DisableReason(StrEnum):
    UNSUPPORTED_TARGET = "unsupported_target"
    SLACK_DISCONNECTED = "slack_disconnected"
    SLACK_PERMISSION_REVOKED = "slack_permission_revoked"
    SLACK_FILE_UPLOAD_PERMISSION_REVOKED = "slack_file_upload_permission_revoked"
    WEBHOOK_REJECTED = "webhook_rejected"
    AI_CONSENT_REVOKED = "ai_consent_revoked"
    AI_PROMPT_INVALID = "ai_prompt_invalid"


UNSUPPORTED_TARGET_DISABLE_REASON = DisableReason.UNSUPPORTED_TARGET
SLACK_DISCONNECTED_DISABLE_REASON = DisableReason.SLACK_DISCONNECTED
SLACK_PERMISSION_REVOKED_DISABLE_REASON = DisableReason.SLACK_PERMISSION_REVOKED
SLACK_FILE_UPLOAD_PERMISSION_REVOKED_DISABLE_REASON = DisableReason.SLACK_FILE_UPLOAD_PERMISSION_REVOKED
WEBHOOK_REJECTED_DISABLE_REASON = DisableReason.WEBHOOK_REJECTED
AI_CONSENT_REVOKED_DISABLE_REASON = DisableReason.AI_CONSENT_REVOKED
AI_PROMPT_INVALID_DISABLE_REASON = DisableReason.AI_PROMPT_INVALID


def get_subscription_disable_reason(*args: Any, **kwargs: Any) -> DisableReason | None:
    return None


def disable_invalid_subscription(*args: Any, **kwargs: Any) -> None:
    return None
