from typing import Any

from pydantic import BaseModel


class MCPToolResult(BaseModel):
    content: Any = None
    structured_content: dict[str, Any] | None = None


class _EmptyRegistry:
    """No MCP tools are registered in the FOSS build; the API answers with not-found."""

    def get(self, *args: Any, **kwargs: Any) -> None:
        return None

    def get_scopes(self, *args: Any, **kwargs: Any) -> list[str]:
        return []

    def list(self, *args: Any, **kwargs: Any) -> list[Any]:
        return []

    def __iter__(self) -> Any:
        return iter(())

    def __contains__(self, item: Any) -> bool:
        return False


mcp_tool_registry = _EmptyRegistry()
