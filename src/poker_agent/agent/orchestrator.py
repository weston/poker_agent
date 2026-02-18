"""Agent orchestrator - main conversation loop."""

from typing import Any, AsyncGenerator

from ..domain.prompts import get_system_prompt
from ..domain.user_profile import UserProfile
from ..llm.base import LLMProvider, Response
from ..tools.base import ToolRegistry
from .message import MessageHistory


class AgentOrchestrator:
    """
    Main agent orchestrator that manages the conversation loop.

    Handles:
    - Message history management
    - LLM interactions
    - Tool execution
    - Response generation
    """

    def __init__(
        self,
        llm: LLMProvider,
        tools: ToolRegistry,
        user_profile: UserProfile | None = None,
        max_tool_iterations: int = 10,
    ):
        """
        Initialize the orchestrator.

        Args:
            llm: LLM provider to use
            tools: Tool registry with available tools
            user_profile: Optional user profile for customization
            max_tool_iterations: Maximum tool call iterations per turn
        """
        self.llm = llm
        self.tools = tools
        self.user_profile = user_profile
        self.max_tool_iterations = max_tool_iterations

        # Initialize message history with system prompt
        system_prompt = get_system_prompt(user_profile)
        self.history = MessageHistory(system_prompt)

    async def process_message(self, user_input: str) -> AsyncGenerator[str, None]:
        """
        Process a user message and yield response chunks.

        This is the main agent loop:
        1. Add user message to history
        2. Call LLM with tools
        3. If tool calls: execute tools, add results, repeat
        4. Yield final text response

        Args:
            user_input: User's message

        Yields:
            Response text chunks
        """
        self.history.add_user(user_input)

        for _ in range(self.max_tool_iterations):
            # Get LLM response
            response = await self.llm.chat(
                messages=self.history.to_list(),
                tools=self.tools.to_list() if self.tools.list_tools() else None,
            )

            if response.has_tool_calls:
                # Add assistant's tool call message to history
                assistant_msg = self.llm.format_assistant_tool_calls(response)
                self.history.add_assistant(
                    content=response.content,
                    raw_content=assistant_msg.get("content"),
                    tool_calls=assistant_msg.get("tool_calls"),
                )

                # Execute each tool and add results
                for tool_call in response.tool_calls:
                    yield f"\n[Using tool: {tool_call.name}]\n"

                    result = await self.tools.execute(
                        tool_call.name, **tool_call.arguments
                    )

                    # Format result for provider
                    tool_result_msg = self.llm.format_tool_result(
                        tool_call.id, result.to_string()
                    )
                    self.history.add_tool_result(
                        tool_call_id=tool_call.id,
                        content=result.to_string(),
                        raw_content=tool_result_msg.get("content"),
                    )

                # If there was also text content, yield it
                if response.content:
                    yield response.content

                # Continue loop to let LLM process tool results
                continue
            else:
                # No tool calls - yield the response and exit
                if response.content:
                    self.history.add_assistant(content=response.content)
                    yield response.content
                break

    async def process_message_simple(self, user_input: str) -> str:
        """
        Process a user message and return complete response.

        Simpler interface that collects all chunks into a single string.

        Args:
            user_input: User's message

        Returns:
            Complete response text
        """
        chunks = []
        async for chunk in self.process_message(user_input):
            chunks.append(chunk)
        return "".join(chunks)

    def clear_history(self) -> None:
        """Clear conversation history (keeps system prompt)."""
        self.history.clear(keep_system=True)

    def update_user_profile(self, profile: UserProfile) -> None:
        """Update user profile and refresh system prompt."""
        self.user_profile = profile
        system_prompt = get_system_prompt(profile)
        self.history.clear(keep_system=False)
        self.history = MessageHistory(system_prompt)
