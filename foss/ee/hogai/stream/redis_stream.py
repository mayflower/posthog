from typing import Any

from ee._foss import unavailable_class

CONVERSATION_STREAM_PREFIX = "conversation-stream:"


def get_conversation_stream_key(conversation_id: Any) -> str:
    return f"{CONVERSATION_STREAM_PREFIX}{conversation_id}"


ConversationRedisStream = unavailable_class("ConversationRedisStream", "PostHog AI")
