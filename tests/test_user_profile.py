"""Tests for user profile."""

import json
import tempfile
from pathlib import Path

import pytest

from poker_agent.domain.user_profile import UserProfile, load_user_profile, save_user_profile


class TestUserProfile:
    def test_default_values(self):
        profile = UserProfile()
        assert profile.definitions == {}
        assert profile.instructions == []
        assert profile.context == ""
        assert profile.player_name == ""

    def test_add_definition(self):
        profile = UserProfile()
        profile.add_definition("Villain", "Main opponent")
        assert profile.definitions["Villain"] == "Main opponent"

    def test_remove_definition(self):
        profile = UserProfile(definitions={"test": "value"})
        assert profile.remove_definition("test")
        assert "test" not in profile.definitions

    def test_remove_nonexistent_definition(self):
        profile = UserProfile()
        assert not profile.remove_definition("nonexistent")

    def test_add_instruction(self):
        profile = UserProfile()
        profile.add_instruction("Always use BB/100")
        assert "Always use BB/100" in profile.instructions

    def test_add_duplicate_instruction(self):
        profile = UserProfile()
        profile.add_instruction("test")
        profile.add_instruction("test")
        assert len(profile.instructions) == 1

    def test_remove_instruction(self):
        profile = UserProfile(instructions=["test"])
        assert profile.remove_instruction("test")
        assert "test" not in profile.instructions

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "profile.json"

            profile = UserProfile(
                player_name="TestPlayer",
                context="I play NL200 6-max",
                definitions={"Fish": "Weak player"},
                instructions=["Focus on exploitative play"],
            )
            profile.save(path)

            loaded = UserProfile.load(path)
            assert loaded.player_name == "TestPlayer"
            assert loaded.context == "I play NL200 6-max"
            assert loaded.definitions["Fish"] == "Weak player"
            assert "Focus on exploitative play" in loaded.instructions

    def test_load_nonexistent_file(self):
        path = Path("/nonexistent/path/profile.json")
        profile = UserProfile.load(path)
        assert profile.player_name == ""  # Default values

    def test_to_dict(self):
        profile = UserProfile(player_name="Test")
        d = profile.to_dict()
        assert d["player_name"] == "Test"
        assert "definitions" in d
        assert "instructions" in d
