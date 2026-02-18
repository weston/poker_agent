"""Statistical analysis tools."""

from typing import Any

from ..base import Tool, ToolResult, registry


class CalculateEVTool(Tool):
    """Tool for calculating expected value of poker decisions."""

    @property
    def name(self) -> str:
        return "calculate_ev"

    @property
    def description(self) -> str:
        return (
            "Calculate the expected value (EV) of a poker decision. "
            "Provide the possible outcomes with their probabilities and payoffs."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "outcomes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "probability": {
                                "type": "number",
                                "description": "Probability of this outcome (0-1)",
                            },
                            "payoff": {
                                "type": "number",
                                "description": "Payoff if this outcome occurs (can be negative for losses)",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of this outcome",
                            },
                        },
                        "required": ["probability", "payoff"],
                    },
                    "description": "List of possible outcomes with probabilities and payoffs",
                },
                "pot_size": {
                    "type": "number",
                    "description": "Current pot size (for context)",
                },
                "bet_size": {
                    "type": "number",
                    "description": "Size of bet being considered (for context)",
                },
            },
            "required": ["outcomes"],
        }

    async def execute(
        self,
        outcomes: list[dict[str, Any]],
        pot_size: float | None = None,
        bet_size: float | None = None,
    ) -> ToolResult:
        """Calculate EV from outcomes."""
        try:
            # Validate probabilities sum to ~1
            total_prob = sum(o["probability"] for o in outcomes)
            if abs(total_prob - 1.0) > 0.01:
                return ToolResult(
                    success=False,
                    error=f"Probabilities should sum to 1.0, got {total_prob:.3f}",
                )

            # Calculate EV
            ev = sum(o["probability"] * o["payoff"] for o in outcomes)

            # Build result
            result_lines = ["EV Calculation:"]
            for o in outcomes:
                desc = o.get("description", "Outcome")
                result_lines.append(
                    f"  {desc}: {o['probability']:.1%} × {o['payoff']:+.2f} = {o['probability'] * o['payoff']:+.2f}"
                )

            result_lines.append(f"\nTotal EV: {ev:+.2f}")

            if pot_size is not None:
                result_lines.append(f"Pot Size: {pot_size:.2f}")
            if bet_size is not None:
                result_lines.append(f"Bet Size: {bet_size:.2f}")
                if pot_size is not None:
                    required_equity = bet_size / (pot_size + bet_size)
                    result_lines.append(
                        f"Required Equity to Call: {required_equity:.1%}"
                    )

            return ToolResult(success=True, data="\n".join(result_lines))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Create and register tool
calculate_ev_tool = CalculateEVTool()
registry.register(calculate_ev_tool)
