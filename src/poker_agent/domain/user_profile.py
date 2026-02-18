"""User profile management for custom definitions and instructions."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile containing custom definitions and instructions."""

    # Custom terminology definitions
    definitions: dict[str, str] = Field(
        default_factory=dict,
        description="User's custom definitions for terms. Example: {'Villain': 'My main opponent in the session'}",
    )

    # Custom instructions for the agent
    instructions: list[str] = Field(
        default_factory=list,
        description="List of custom instructions for the agent to follow",
    )

    # Additional context about the user
    context: str = Field(
        default="",
        description="Additional context about the user's play style, stakes, games, etc.",
    )

    # User's player name for auto-lookup
    player_name: str = Field(
        default="",
        description="User's screen name for automatic stat lookups",
    )

    # Preferred stakes/games
    preferred_games: list[str] = Field(
        default_factory=list,
        description="User's preferred game types (e.g., 'NL200', '6-max', 'MTT')",
    )

    def add_definition(self, term: str, definition: str) -> None:
        """Add a custom definition."""
        self.definitions[term] = definition

    def remove_definition(self, term: str) -> bool:
        """Remove a definition. Returns True if removed."""
        if term in self.definitions:
            del self.definitions[term]
            return True
        return False

    def add_instruction(self, instruction: str) -> None:
        """Add a custom instruction."""
        if instruction not in self.instructions:
            self.instructions.append(instruction)

    def remove_instruction(self, instruction: str) -> bool:
        """Remove an instruction. Returns True if removed."""
        if instruction in self.instructions:
            self.instructions.remove(instruction)
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def save(self, path: Path) -> None:
        """Save profile to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.model_dump(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "UserProfile":
        """Load profile from JSON file."""
        if not path.exists():
            return cls()
        with open(path) as f:
            data = json.load(f)
        return cls(**data)


def get_default_profile_path() -> Path:
    """Get the default profile path."""
    return Path.home() / ".poker_agent" / "profile.json"


def load_user_profile(path: Path | None = None) -> UserProfile:
    """
    Load user profile from file.

    Args:
        path: Optional custom path. Uses default if not provided.

    Returns:
        UserProfile instance
    """
    profile_path = path or get_default_profile_path()
    return UserProfile.load(profile_path)


def save_user_profile(profile: UserProfile, path: Path | None = None) -> None:
    """
    Save user profile to file.

    Args:
        profile: Profile to save
        path: Optional custom path. Uses default if not provided.
    """
    profile_path = path or get_default_profile_path()
    profile.save(profile_path)
