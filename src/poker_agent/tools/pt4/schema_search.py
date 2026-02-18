"""PT4 schema documentation search tool.

This module provides a tool for searching PT4 column definitions
to help the agent build accurate database queries.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..base import Tool, ToolResult, registry


@dataclass
class ColumnDefinition:
    """A PT4 column definition."""

    name: str
    formula: str
    description: str
    source_file: str

    def matches(self, keywords: list[str]) -> int:
        """
        Check if this definition matches the keywords.
        Returns a score (higher = better match).
        """
        text = f"{self.name} {self.description}".lower()
        score = 0
        for kw in keywords:
            kw_lower = kw.lower()
            # Exact name match is worth more
            if kw_lower == self.name.lower():
                score += 10
            elif kw_lower in self.name.lower():
                score += 5
            elif kw_lower in text:
                score += 1
        return score


class SchemaIndex:
    """Index of PT4 schema definitions for fast searching."""

    def __init__(self):
        self.definitions: list[ColumnDefinition] = []
        self._loaded = False

    def _load_handstats(self, path: Path) -> None:
        """Parse handstats_definitions.txt format."""
        content = path.read_text(encoding="utf-8")
        # Format:
        # Name:
        #     column_name
        #     Description text
        #
        # Split by double newline to get entries
        entries = content.split("\n\n")

        current_name = None
        for entry in entries:
            lines = [l for l in entry.strip().split("\n") if l.strip()]
            if not lines:
                continue

            # First line is display name (with colon)
            if lines[0].endswith(":"):
                current_name = lines[0].rstrip(":")
                if len(lines) >= 2:
                    formula = lines[1].strip()
                    description = " ".join(l.strip() for l in lines[2:]) if len(lines) > 2 else ""
                    self.definitions.append(ColumnDefinition(
                        name=formula,  # Use column name as the name
                        formula=formula,
                        description=f"{current_name}: {description}",
                        source_file="handstats",
                    ))
            elif len(lines) >= 2:
                # Some entries don't have the : format
                formula = lines[0].strip()
                description = " ".join(l.strip() for l in lines[1:])
                self.definitions.append(ColumnDefinition(
                    name=formula,
                    formula=formula,
                    description=description,
                    source_file="handstats",
                ))

    def _load_cash_player_columns(self, path: Path) -> None:
        """Parse cash_player_columns_definition.txt format."""
        content = path.read_text(encoding="utf-8")
        # Format:
        # column_name
        #     formula
        #     description
        #
        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Column name (not indented)
            if not lines[i].startswith("\t") and not lines[i].startswith("    "):
                name = line
                formula = ""
                description = ""

                # Next line should be formula (indented)
                if i + 1 < len(lines):
                    formula = lines[i + 1].strip()
                    i += 1

                # Following line(s) should be description (indented)
                if i + 1 < len(lines):
                    desc_lines = []
                    i += 1
                    while i < len(lines) and (lines[i].startswith("\t") or lines[i].startswith("    ") or not lines[i].strip()):
                        if lines[i].strip():
                            desc_lines.append(lines[i].strip())
                        i += 1
                    description = " ".join(desc_lines)

                self.definitions.append(ColumnDefinition(
                    name=name,
                    formula=formula,
                    description=description,
                    source_file="cash_player_columns",
                ))
            else:
                i += 1

    def load(self) -> None:
        """Load all schema definitions."""
        if self._loaded:
            return

        schema_dir = Path(__file__).parent / "schema_docs"

        handstats_path = schema_dir / "handstats_definitions.txt"
        if handstats_path.exists():
            self._load_handstats(handstats_path)

        cash_cols_path = schema_dir / "cash_player_columns_definition.txt"
        if cash_cols_path.exists():
            self._load_cash_player_columns(cash_cols_path)

        self._loaded = True

    def search(
        self,
        keywords: list[str],
        max_results: int = 20,
        source: str | None = None,
    ) -> list[ColumnDefinition]:
        """
        Search for columns matching keywords.

        Args:
            keywords: List of search terms
            max_results: Maximum number of results
            source: Filter by source file ("handstats" or "cash_player_columns")

        Returns:
            List of matching ColumnDefinitions, sorted by relevance
        """
        self.load()

        results = []
        for defn in self.definitions:
            if source and defn.source_file != source:
                continue
            score = defn.matches(keywords)
            if score > 0:
                results.append((score, defn))

        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [defn for _, defn in results[:max_results]]

    def list_categories(self) -> dict[str, int]:
        """Get a count of columns by prefix category."""
        self.load()
        categories: dict[str, int] = {}
        for defn in self.definitions:
            # Extract prefix (e.g., "flg_", "amt_", "cnt_")
            match = re.match(r"^([a-z]+_)", defn.name)
            if match:
                prefix = match.group(1)
                categories[prefix] = categories.get(prefix, 0) + 1
        return categories


# Singleton index
_schema_index: SchemaIndex | None = None


def get_schema_index() -> SchemaIndex:
    """Get the schema index singleton."""
    global _schema_index
    if _schema_index is None:
        _schema_index = SchemaIndex()
    return _schema_index


class SearchPT4SchemasTool(Tool):
    """Tool for searching PT4 column definitions."""

    @property
    def name(self) -> str:
        return "search_pt4_schema"

    @property
    def description(self) -> str:
        return (
            "Search PokerTracker 4 database column definitions to find the correct "
            "column names and understand their meaning. Use this BEFORE writing PT4 "
            "queries to ensure you use the correct column names. "
            "Common prefixes: flg_ (boolean flags), amt_ (amounts), cnt_ (counts), "
            "val_ (values), enum_ (enumerations)."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Search keywords. Examples: ['vpip'], ['3bet', 'preflop'], "
                        "['cbet', 'flop'], ['fold', 'river'], ['won', 'amount']"
                    ),
                },
                "source": {
                    "type": "string",
                    "enum": ["handstats", "cash_player_columns", "all"],
                    "description": (
                        "Which schema to search. 'handstats' for hand-level data, "
                        "'cash_player_columns' for aggregated player statistics, "
                        "'all' for both."
                    ),
                    "default": "all",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 15,
                },
            },
            "required": ["keywords"],
        }

    async def execute(
        self,
        keywords: list[str],
        source: str = "all",
        max_results: int = 15,
    ) -> ToolResult:
        """Search the schema index."""
        try:
            index = get_schema_index()
            source_filter = None if source == "all" else source

            results = index.search(
                keywords=keywords,
                max_results=max_results,
                source=source_filter,
            )

            if not results:
                return ToolResult(
                    success=True,
                    data=f"No columns found matching: {', '.join(keywords)}",
                )

            # Format results
            lines = [f"Found {len(results)} matching columns:\n"]
            for defn in results:
                lines.append(f"**{defn.name}**")
                if defn.formula and defn.formula != defn.name:
                    lines.append(f"  Formula: `{defn.formula}`")
                lines.append(f"  {defn.description}")
                lines.append(f"  Source: {defn.source_file}")
                lines.append("")

            return ToolResult(success=True, data="\n".join(lines))

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ListPT4ColumnCategoriesTool(Tool):
    """Tool for listing PT4 column categories."""

    @property
    def name(self) -> str:
        return "list_pt4_column_categories"

    @property
    def description(self) -> str:
        return (
            "List the categories of columns available in PT4 database by their "
            "prefix (e.g., flg_ for flags, amt_ for amounts). Useful for "
            "understanding what types of data are available."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

    async def execute(self) -> ToolResult:
        """List column categories."""
        try:
            index = get_schema_index()
            categories = index.list_categories()

            lines = ["PT4 Column Categories:\n"]
            prefix_descriptions = {
                "flg_": "Boolean flags (true/false conditions)",
                "amt_": "Monetary amounts",
                "cnt_": "Counts/frequencies",
                "val_": "Calculated values",
                "enum_": "Enumerated values (categories)",
                "str_": "String/text values",
                "id_": "Identifiers/references",
            }

            for prefix, count in sorted(categories.items(), key=lambda x: -x[1]):
                desc = prefix_descriptions.get(prefix, "")
                lines.append(f"  {prefix}* : {count} columns {f'- {desc}' if desc else ''}")

            return ToolResult(success=True, data="\n".join(lines))

        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Create and register tools
search_pt4_schema_tool = SearchPT4SchemasTool()
list_pt4_categories_tool = ListPT4ColumnCategoriesTool()

registry.register(search_pt4_schema_tool)
registry.register(list_pt4_categories_tool)
