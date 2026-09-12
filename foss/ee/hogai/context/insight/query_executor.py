from typing import Any

from pydantic import BaseModel

from ee._foss import unavailable_class


class FormattedQueryResult(BaseModel):
    content: Any = None


AssistantQueryExecutor = unavailable_class("AssistantQueryExecutor", "PostHog AI")
