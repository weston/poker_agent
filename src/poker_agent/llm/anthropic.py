"""Anthropic LLM provider implementation."""

import json
from typing import Any

import anthropic

from .base import LLMProvider, Response, ToolCall


class AnthropicProvider(LLMProvider):
    """Anthropic API provider implementation."""

    def __init__(
        self, api_key: str, default_model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            default_model: Default model to use
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.default_model = default_model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> Response:
        """Send messages to Anthropic and get response."""
        # Extract system message if present
        system_content = None
        chat_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                chat_messages.append(msg)

        kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "max_tokens": 4096,
            "messages": chat_messages,
        }

        if system_content:
            kwargs["system"] = system_content

        if tools:
            # Convert to Anthropic tool format
            kwargs["tools"] = [
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["parameters"],
                }
                for tool in tools
            ]

        response = await self.client.messages.create(**kwargs)

        # Parse response content
        content_text = None
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content_text = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input,
                    )
                )

        return Response(
            content=content_text,
            tool_calls=tool_calls,
            raw_response=response,
            finish_reason=response.stop_reason,
        )

    def format_tool_result(
        self, tool_call_id: str, result: str
    ) -> dict[str, Any]:
        """Format tool result for Anthropic message format."""
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": result,
                }
            ],
        }

    def format_assistant_tool_calls(
        self, response: Response
    ) -> dict[str, Any]:
        """Format assistant message with tool calls for Anthropic."""
        content = []

        if response.content:
            content.append({"type": "text", "text": response.content})

        for tc in response.tool_calls:
            content.append(
                {
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                }
            )

        return {"role": "assistant", "content": content}
