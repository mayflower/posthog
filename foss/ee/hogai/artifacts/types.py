from typing import Any

from pydantic import BaseModel


class ModelArtifactResult(BaseModel):
    content: Any = None
