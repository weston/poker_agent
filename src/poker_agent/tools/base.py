"""Tool base class and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """Result from tool execution."""

    success: bool
    data: Any = None
    error: str | None = None

    def to_string(self) -> str:
        """Convert result to string for LLM consumption."""
        if self.success:
            if isinstance(self.data, str):
                return self.data
            return str(self.data)
        return f"Error: {self.error}"


class Tool(ABC):
    """Abstract base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does (shown to LLM)."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema for tool parameters."""
        pass

    @abstractmethod
    async def execute(self, **params: Any) -> ToolResult:
        """
        Execute the tool with given parameters.

        Args:
            **params: Tool-specific parameters

        Returns:
            ToolResult with success/failure and data
        """
        pass

    def to_dict(self) -> dict[str, Any]:
        """Convert tool to dictionary format for LLM."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        """List all registered tools."""
        return list(self._tools.values())

    def to_list(self) -> list[dict[str, Any]]:
        """Convert all tools to list of dicts for LLM."""
        return [tool.to_dict() for tool in self._tools.values()]

    async def execute(self, name: str, **params: Any) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            **params: Tool parameters

        Returns:
            ToolResult from execution
        """
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False, error=f"Unknown tool: {name}"
            )

        try:
            return await tool.execute(**params)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Global tool registry
registry = ToolRegistry()
