"""OpenAI LLM provider implementation."""

import json
from typing import Any

from openai import AsyncOpenAI

from .base import LLMProvider, Response, ToolCall


class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation."""

    def __init__(self, api_key: str, default_model: str = "gpt-4o"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            default_model: Default model to use
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.default_model = default_model

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> Response:
        """Send messages to OpenAI and get response."""
        kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
        }

        if tools:
            # Convert to OpenAI tool format
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    },
                }
                for tool in tools
            ]

        response = await self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    )
                )

        return Response(
            content=message.content,
            tool_calls=tool_calls,
            raw_response=response,
            finish_reason=response.choices[0].finish_reason,
        )

    def format_tool_result(
        self, tool_call_id: str, result: str
    ) -> dict[str, Any]:
        """Format tool result for OpenAI message format."""
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result,
        }

    def format_assistant_tool_calls(
        self, response: Response
    ) -> dict[str, Any]:
        """Format assistant message with tool calls for OpenAI."""
        return {
            "role": "assistant",
            "content": response.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                }
                for tc in response.tool_calls
            ],
        }
