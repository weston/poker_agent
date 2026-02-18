"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Response:
    """Response from an LLM provider."""

    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw_response: Any = None
    finish_reason: str | None = None

    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> Response:
        """
        Send messages to the LLM and get a response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions
            model: Optional model override

        Returns:
            Response object with content and/or tool calls
        """
        pass

    @abstractmethod
    def format_tool_result(
        self, tool_call_id: str, result: str
    ) -> dict[str, Any]:
        """
        Format a tool result for inclusion in message history.

        Args:
            tool_call_id: The ID of the tool call this result is for
            result: The string result of the tool execution

        Returns:
            Message dict formatted for this provider
        """
        pass

    @abstractmethod
    def format_assistant_tool_calls(
        self, response: Response
    ) -> dict[str, Any]:
        """
        Format an assistant response with tool calls for message history.

        Args:
            response: The Response object containing tool calls

        Returns:
            Message dict formatted for this provider
        """
        pass
