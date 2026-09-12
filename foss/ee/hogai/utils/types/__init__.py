from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from .base import AssistantNodeName, NodePath


class AssistantMode(StrEnum):
    ASSISTANT = "assistant"
    INSIGHTS_TOOL = "insights_tool"


class AssistantState(BaseModel):
    model_config = {"extra": "allow"}


AssistantOutput = tuple[str, Any]

__all__ = ["AssistantMode", "AssistantNodeName", "AssistantOutput", "AssistantState", "NodePath"]
