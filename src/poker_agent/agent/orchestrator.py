"""Agent orchestrator - main conversation loop."""

from dataclasses import dataclass
from typing import Any, AsyncGenerator

from ..domain.prompts import get_system_prompt
from ..domain.user_profile import UserProfile
from ..llm.base import LLMProvider, Response, get_context_limit
from ..tools.base import ToolRegistry
from .message import MessageHistory


@dataclass
class ContextUsage:
    """Tracks context window usage."""

    total_tokens: int
    context_limit: int

    @property
    def percentage(self) -> float:
        """Get usage as percentage."""
        if self.context_limit == 0:
            return 0.0
        return (self.total_tokens / self.context_limit) * 100

    @property
    def formatted(self) -> str:
        """Get formatted usage string."""
        return f"{self.percentage:.1f}% ({self.total_tokens:,} / {self.context_limit:,} tokens)"


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
        max_tool_iterations: int = 50,
    ):
        """
        Initialize the orchestrator.

        Args:
            llm: LLM provider to use
            tools: Tool registry with available tools
            user_profile: Optional user profile for customization
            max_tool_iterations: Maximum tool call iterations per turn (default 50)
        """
        self.llm = llm
        self.tools = tools
        self.user_profile = user_profile
        self.max_tool_iterations = max_tool_iterations

        # Initialize message history with system prompt
        system_prompt = get_system_prompt(user_profile)
        self.history = MessageHistory(system_prompt)

        # Token tracking
        self._last_input_tokens = 0  # Most recent input token count (reflects context size)
        self._total_output_tokens = 0  # Cumulative output tokens

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

        yielded_response = False

        for iteration in range(self.max_tool_iterations):
            # Get LLM response
            response = await self.llm.chat(
                messages=self.history.to_list(),
                tools=self.tools.to_list() if self.tools.list_tools() else None,
            )

            # Track token usage
            self._last_input_tokens = response.input_tokens
            self._total_output_tokens += response.output_tokens

            if response.has_tool_calls:
                # Add assistant's tool call message to history
                assistant_msg = self.llm.format_assistant_tool_calls(response)
                self.history.add_assistant(
                    content=response.content,
                    raw_message=assistant_msg,
                )

                # Execute all tools and collect results
                tool_results = []
                for tool_call in response.tool_calls:
                    yield f"\n[Using tool: {tool_call.name}]\n"

                    result = await self.tools.execute(
                        tool_call.name, **tool_call.arguments
                    )
                    tool_results.append((tool_call.id, result.to_string()))

                # Add tool results as message(s)
                # Anthropic: single message with all results
                # OpenAI: separate message per result
                tool_result_msgs = self.llm.format_tool_results(tool_results)
                for msg in tool_result_msgs:
                    self.history.add_tool_result(
                        tool_call_id=tool_results[0][0],
                        content=str([r[1] for r in tool_results]),
                        raw_message=msg,
                    )

                # Continue loop to let LLM process tool results
                continue
            else:
                # No tool calls - yield the response and exit
                if response.content:
                    self.history.add_assistant(content=response.content)
                    yield response.content
                    yielded_response = True
                break

        # If we never yielded a response, something went wrong
        if not yielded_response:
            debug_info = (
                f"finish_reason: {response.finish_reason}, "
                f"has_tool_calls: {response.has_tool_calls}, "
                f"content: {response.content[:100] if response.content else None}, "
                f"iterations: {iteration + 1}/{self.max_tool_iterations}"
            )
            error_msg = f"[No response generated. Debug: {debug_info}]"
            yield error_msg

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
        self._last_input_tokens = 0
        self._total_output_tokens = 0

    def get_context_usage(self) -> ContextUsage:
        """Get current context window usage."""
        model = self.llm.default_model
        context_limit = get_context_limit(model)
        # Use last input tokens as the best estimate of current context size
        return ContextUsage(
            total_tokens=self._last_input_tokens,
            context_limit=context_limit,
        )

    def update_user_profile(self, profile: UserProfile) -> None:
        """Update user profile and refresh system prompt."""
        self.user_profile = profile
        system_prompt = get_system_prompt(profile)
        self.history.clear(keep_system=False)
        self.history = MessageHistory(system_prompt)
