from typing import Any

from pydantic import BaseModel

from ee._foss import EnterpriseFeatureUnavailable


class ClientToolCallRequest(BaseModel):
    tool_name: str = ""
    arguments: dict[str, Any] = {}


class ApprovalResumePayload(BaseModel):
    approved: bool = False


class MaxTool:
    """Base class for Max tools. Subclasses declare ``name``, ``description`` and ``args_schema``.

    The agent that would run these tools is enterprise-only, so instances cannot be created here.
    """

    name: str = ""
    description: str = ""
    args_schema: type[BaseModel] | None = None
    context_prompt_template: str = ""
    thinking_message: str = ""
    show_tool_call_message: bool = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise EnterpriseFeatureUnavailable("PostHog AI")

    def __class_getitem__(cls, item: Any) -> type:
        return cls
