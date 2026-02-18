"""Message types and history management."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageRole(Enum):
    """Message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A message in the conversation."""

    role: MessageRole
    content: str
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    raw_content: Any = None  # For provider-specific content
    raw_message: dict[str, Any] | None = None  # Complete provider-specific message

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API calls."""
        # If we have a complete raw message from the provider, use it directly
        if self.raw_message is not None:
            return self.raw_message

        result: dict[str, Any] = {"role": self.role.value}

        if self.raw_content is not None:
            result["content"] = self.raw_content
        else:
            result["content"] = self.content

        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id

        if self.tool_calls:
            result["tool_calls"] = self.tool_calls

        return result


class MessageHistory:
    """Manages conversation message history."""

    def __init__(self, system_prompt: str | None = None):
        """
        Initialize message history.

        Args:
            system_prompt: Optional system prompt to start with
        """
        self._messages: list[Message] = []
        if system_prompt:
            self._messages.append(
                Message(role=MessageRole.SYSTEM, content=system_prompt)
            )

    def add(self, message: Message) -> None:
        """Add a message to history."""
        self._messages.append(message)

    def add_user(self, content: str) -> None:
        """Add a user message."""
        self.add(Message(role=MessageRole.USER, content=content))

    def add_assistant(
        self,
        content: str | None = None,
        raw_message: dict[str, Any] | None = None,
    ) -> None:
        """Add an assistant message."""
        self.add(
            Message(
                role=MessageRole.ASSISTANT,
                content=content or "",
                raw_message=raw_message,
            )
        )

    def add_tool_result(
        self,
        tool_call_id: str,
        content: str,
        raw_message: dict[str, Any] | None = None,
    ) -> None:
        """Add a tool result message."""
        self.add(
            Message(
                role=MessageRole.TOOL,
                content=content,
                tool_call_id=tool_call_id,
                raw_message=raw_message,
            )
        )

    def to_list(self) -> list[dict[str, Any]]:
        """Convert all messages to list of dicts."""
        return [msg.to_dict() for msg in self._messages]

    def clear(self, keep_system: bool = True) -> None:
        """Clear message history."""
        if keep_system and self._messages and self._messages[0].role == MessageRole.SYSTEM:
            system_msg = self._messages[0]
            self._messages = [system_msg]
        else:
            self._messages = []

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self):
        return iter(self._messages)
