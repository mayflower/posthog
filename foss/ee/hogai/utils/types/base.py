from enum import StrEnum


class AssistantNodeName(StrEnum):
    ROOT = "root"
    WEB_ANALYTICS_FILTER = "web_analytics_filter"
    WEB_ANALYTICS_FILTER_OPTIONS_TOOLS = "web_analytics_filter_options_tools"


NodePath = tuple[str, ...]
