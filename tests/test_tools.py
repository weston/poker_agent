"""Tests for tool system."""

import pytest

from poker_agent.tools.base import Tool, ToolRegistry, ToolResult


class MockTool(Tool):
    """A mock tool for testing."""

    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "A mock tool for testing"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
            },
            "required": ["value"],
        }

    async def execute(self, value: str) -> ToolResult:
        return ToolResult(success=True, data=f"Received: {value}")


class FailingTool(Tool):
    """A tool that always fails."""

    @property
    def name(self) -> str:
        return "failing_tool"

    @property
    def description(self) -> str:
        return "A tool that always fails"

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    async def execute(self) -> ToolResult:
        raise ValueError("Intentional failure")


class TestToolResult:
    def test_success_to_string(self):
        result = ToolResult(success=True, data="test data")
        assert result.to_string() == "test data"

    def test_error_to_string(self):
        result = ToolResult(success=False, error="test error")
        assert result.to_string() == "Error: test error"


class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)

        assert registry.get("mock_tool") is tool

    def test_get_unknown_tool(self):
        registry = ToolRegistry()
        assert registry.get("unknown") is None

    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register(MockTool())
        tools = registry.list_tools()
        assert len(tools) == 1

    def test_to_list(self):
        registry = ToolRegistry()
        registry.register(MockTool())
        tool_dicts = registry.to_list()

        assert len(tool_dicts) == 1
        assert tool_dicts[0]["name"] == "mock_tool"
        assert "description" in tool_dicts[0]
        assert "parameters" in tool_dicts[0]

    @pytest.mark.asyncio
    async def test_execute_success(self):
        registry = ToolRegistry()
        registry.register(MockTool())

        result = await registry.execute("mock_tool", value="hello")
        assert result.success
        assert result.data == "Received: hello"

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        registry = ToolRegistry()

        result = await registry.execute("unknown_tool")
        assert not result.success
        assert "Unknown tool" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_exception(self):
        registry = ToolRegistry()
        registry.register(FailingTool())

        result = await registry.execute("failing_tool")
        assert not result.success
        assert "Intentional failure" in result.error

    def test_unregister(self):
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.unregister("mock_tool")

        assert registry.get("mock_tool") is None
