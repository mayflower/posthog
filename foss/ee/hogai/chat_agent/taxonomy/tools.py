from typing import Any

from pydantic import BaseModel


class TaxonomyTool(BaseModel):
    def __class_getitem__(cls, item: Any) -> type:
        return cls


class base_final_answer(BaseModel):
    """Final answer of a taxonomy agent. Products subclass this with their own filter model."""

    def __class_getitem__(cls, item: Any) -> type:
        return cls


class ask_user_for_help(BaseModel):
    request: str = ""
