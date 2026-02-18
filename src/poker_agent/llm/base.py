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
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return len(self.tool_calls) > 0

    @property
    def total_tokens(self) -> int:
        """Total tokens used in this response."""
        return self.input_tokens + self.output_tokens


# Context window limits for common models
MODEL_CONTEXT_LIMITS: dict[str, int] = {
    # Anthropic models
    "claude-sonnet-4-20250514": 200_000,
    "claude-opus-4-20250514": 200_000,
    "claude-3-5-sonnet-20241022": 200_000,
    "claude-3-opus-20240229": 200_000,
    "claude-3-sonnet-20240229": 200_000,
    "claude-3-haiku-20240307": 200_000,
    # OpenAI models
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 8_192,
    "gpt-3.5-turbo": 16_385,
}


def get_context_limit(model: str) -> int:
    """Get context window limit for a model, defaulting to 100K if unknown."""
    return MODEL_CONTEXT_LIMITS.get(model, 100_000)


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

    @abstractmethod
    def format_tool_results(
        self, results: list[tuple[str, str]]
    ) -> list[dict[str, Any]]:
        """
        Format multiple tool results into message(s).

        Args:
            results: List of (tool_call_id, result_string) tuples

        Returns:
            List of message dicts. Anthropic returns one message with all results,
            OpenAI returns separate messages for each result.
        """
        pass
