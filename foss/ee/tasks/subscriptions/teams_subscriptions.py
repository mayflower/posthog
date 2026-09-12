from typing import Any

from ee._foss import unavailable_function

TEAMS_CARD_TEXT_BUDGET = 28000
TEAMS_UTM_TAGS = "utm_source=posthog&utm_campaign=subscription_report&utm_medium=teams"


def teams_byte_size(value: Any) -> int:
    return len(str(value).encode())


def teams_text_block(text: str, **kwargs: Any) -> dict[str, Any]:
    return {"type": "TextBlock", "text": text, "wrap": True, **kwargs}


def teams_open_url_action(title: str, url: str) -> dict[str, Any]:
    return {"type": "Action.OpenUrl", "title": title, "url": url}


def teams_card_message(body: list[dict[str, Any]], actions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"type": "AdaptiveCard", "body": body, "actions": actions or []}


def fit_to_teams_budget(body: list[dict[str, Any]], *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    return body


build_teams_subscription_card = unavailable_function("build_teams_subscription_card", "Teams subscription delivery")
