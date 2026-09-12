from typing import Any

STOP_REASON_END_TURN = "end_turn"
TURN_COMPLETE_METHOD = "turn_complete"


def is_turn_complete(*args: Any, **kwargs: Any) -> bool:
    return False


def turn_complete_trace_id(*args: Any, **kwargs: Any) -> str | None:
    return None
