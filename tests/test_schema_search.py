"""Tests for PT4 schema search."""

import pytest

from poker_agent.tools.pt4.schema_search import (
    SchemaIndex,
    ColumnDefinition,
    get_schema_index,
)


class TestColumnDefinition:
    def test_matches_exact_name(self):
        defn = ColumnDefinition(
            name="cnt_vpip",
            formula="sum(...)",
            description="VPIP count",
            source_file="test",
        )
        # Exact name match should score higher
        assert defn.matches(["cnt_vpip"]) > defn.matches(["vpip"])

    def test_matches_partial_name(self):
        defn = ColumnDefinition(
            name="cnt_vpip",
            formula="sum(...)",
            description="VPIP count",
            source_file="test",
        )
        assert defn.matches(["vpip"]) > 0

    def test_matches_description(self):
        defn = ColumnDefinition(
            name="cnt_vpip",
            formula="sum(...)",
            description="voluntarily put money in pot",
            source_file="test",
        )
        assert defn.matches(["voluntarily"]) > 0

    def test_no_match(self):
        defn = ColumnDefinition(
            name="cnt_vpip",
            formula="sum(...)",
            description="VPIP count",
            source_file="test",
        )
        assert defn.matches(["xyz123"]) == 0


class TestSchemaIndex:
    def test_load(self):
        index = get_schema_index()
        index.load()
        # Should have loaded definitions from the schema files
        assert len(index.definitions) > 0

    def test_search_vpip(self):
        index = get_schema_index()
        results = index.search(["vpip"])
        assert len(results) > 0
        # First result should have vpip in the name
        assert "vpip" in results[0].name.lower()

    def test_search_3bet(self):
        index = get_schema_index()
        results = index.search(["3bet"])
        assert len(results) > 0

    def test_search_with_source_filter(self):
        index = get_schema_index()
        results_all = index.search(["flg"])
        results_cash = index.search(["flg"], source="cash_player_columns")
        results_hand = index.search(["flg"], source="handstats")

        # Filtered results should be subset
        assert len(results_cash) <= len(results_all)
        assert len(results_hand) <= len(results_all)

    def test_search_max_results(self):
        index = get_schema_index()
        results = index.search(["flg"], max_results=5)
        assert len(results) <= 5

    def test_list_categories(self):
        index = get_schema_index()
        categories = index.list_categories()
        # Should have common prefixes
        assert "flg_" in categories or "cnt_" in categories or "amt_" in categories


class TestSearchTool:
    @pytest.mark.asyncio
    async def test_search_tool_execute(self):
        from poker_agent.tools.pt4.schema_search import search_pt4_schema_tool

        result = await search_pt4_schema_tool.execute(keywords=["vpip"])
        assert result.success
        assert "vpip" in result.data.lower()

    @pytest.mark.asyncio
    async def test_search_tool_no_results(self):
        from poker_agent.tools.pt4.schema_search import search_pt4_schema_tool

        result = await search_pt4_schema_tool.execute(keywords=["xyznonexistent123"])
        assert result.success
        assert "No columns found" in result.data

    @pytest.mark.asyncio
    async def test_list_categories_tool(self):
        from poker_agent.tools.pt4.schema_search import list_pt4_categories_tool

        result = await list_pt4_categories_tool.execute()
        assert result.success
        assert "Categories" in result.data
