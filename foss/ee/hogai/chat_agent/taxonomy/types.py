from typing import Any

from pydantic import BaseModel


class TaxonomyAgentState(BaseModel):
    def __class_getitem__(cls, item: Any) -> type:
        return cls
