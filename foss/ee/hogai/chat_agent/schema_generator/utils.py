from typing import Any

from pydantic import BaseModel


class SchemaGeneratorOutput(BaseModel):
    query: Any = None

    def __class_getitem__(cls, item: Any) -> type:
        return cls
