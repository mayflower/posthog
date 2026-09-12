from dataclasses import dataclass
from typing import Any


@dataclass
class CompactionResult:
    compacted: bool = False


def select_compactable_conversation_ids(*args: Any, **kwargs: Any) -> list[Any]:
    return []


def compact_conversation(*args: Any, **kwargs: Any) -> CompactionResult:
    return CompactionResult()
