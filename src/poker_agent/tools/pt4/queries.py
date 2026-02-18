"""PT4 query tools."""

import json
from typing import Any

from ..base import Tool, ToolResult, registry
from .connection import get_pt4_connection


class QueryPT4Tool(Tool):
    """Tool for executing custom queries against PT4 database."""

    @property
    def name(self) -> str:
        return "query_pt4"

    @property
    def description(self) -> str:
        return (
            "Execute a SQL query against the PokerTracker 4 PostgreSQL database. "
            "Use this for custom queries when the other PT4 tools don't meet your needs. "
            "Common tables: player, cash_hand_player_statistics, tournament_hand_player_statistics."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute. Use parameterized queries with %s placeholders.",
                },
                "params": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Query parameters to substitute for %s placeholders.",
                    "default": [],
                },
            },
            "required": ["query"],
        }

    async def execute(
        self, query: str, params: list[str] | None = None
    ) -> ToolResult:
        """Execute the query."""
        try:
            conn = get_pt4_connection()
            results = await conn.execute_query(
                query, tuple(params) if params else None
            )
            return ToolResult(
                success=True,
                data=json.dumps(results, default=str, indent=2),
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetPlayerStatsTool(Tool):
    """Tool for fetching player statistics."""

    @property
    def name(self) -> str:
        return "get_player_stats"

    @property
    def description(self) -> str:
        return (
            "Get statistics for a specific player from PokerTracker 4. "
            "Returns common stats like VPIP, PFR, 3-bet %, etc."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "player_name": {
                    "type": "string",
                    "description": "The player's screen name to look up.",
                },
                "game_type": {
                    "type": "string",
                    "enum": ["cash", "tournament"],
                    "description": "Type of game stats to retrieve.",
                    "default": "cash",
                },
            },
            "required": ["player_name"],
        }

    async def execute(
        self, player_name: str, game_type: str = "cash"
    ) -> ToolResult:
        """Fetch player statistics."""
        try:
            conn = get_pt4_connection()

            # Query varies based on game type
            if game_type == "cash":
                table = "cash_hand_player_statistics"
            else:
                table = "tournament_hand_player_statistics"

            # Get basic aggregated stats
            query = f"""
                SELECT
                    p.player_name,
                    COUNT(*) as hands,
                    ROUND(100.0 * SUM(CASE WHEN s.flg_vpip THEN 1 ELSE 0 END) / COUNT(*), 1) as vpip,
                    ROUND(100.0 * SUM(CASE WHEN s.flg_p_raise THEN 1 ELSE 0 END) / COUNT(*), 1) as pfr,
                    ROUND(100.0 * SUM(CASE WHEN s.flg_p_3bet THEN 1 ELSE 0 END) /
                          NULLIF(SUM(CASE WHEN s.flg_p_3bet_opp THEN 1 ELSE 0 END), 0), 1) as three_bet,
                    ROUND(100.0 * SUM(CASE WHEN s.flg_p_fold_to_3bet THEN 1 ELSE 0 END) /
                          NULLIF(SUM(CASE WHEN s.flg_p_face_3bet THEN 1 ELSE 0 END), 0), 1) as fold_to_3bet
                FROM {table} s
                JOIN player p ON s.id_player = p.id_player
                WHERE LOWER(p.player_name) = LOWER(%s)
                GROUP BY p.player_name
            """

            results = await conn.execute_query(query, (player_name,))

            if not results:
                return ToolResult(
                    success=True,
                    data=f"No data found for player: {player_name}",
                )

            return ToolResult(
                success=True,
                data=json.dumps(results[0], default=str, indent=2),
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Create tool instances
query_pt4_tool = QueryPT4Tool()
get_player_stats_tool = GetPlayerStatsTool()

# Register tools
registry.register(query_pt4_tool)
registry.register(get_player_stats_tool)
