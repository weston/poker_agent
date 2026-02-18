"""Tests for PT4 utilities."""

import pytest

from poker_agent.tools.pt4.utils import (
    pt4_to_poker_pct,
    poker_to_pt4_pct,
    decode_card,
    decode_board,
    decode_hole_cards,
    parse_action_string,
    format_bet_size,
)


class TestPercentageConversion:
    def test_pt4_to_poker_quarter_pot(self):
        # 20% PT4 ≈ 25% poker
        result = pt4_to_poker_pct(20)
        assert 24 < result < 26

    def test_pt4_to_poker_third_pot(self):
        # 25% PT4 ≈ 33% poker
        result = pt4_to_poker_pct(25)
        assert 32 < result < 35

    def test_pt4_to_poker_half_pot(self):
        # 33% PT4 ≈ 50% poker
        result = pt4_to_poker_pct(33.33)
        assert 49 < result < 51

    def test_pt4_to_poker_pot_sized(self):
        # 50% PT4 = 100% poker
        result = pt4_to_poker_pct(50)
        assert result == 100.0

    def test_pt4_to_poker_overbet(self):
        # 75% PT4 = 300% poker
        result = pt4_to_poker_pct(75)
        assert result == 300.0

    def test_pt4_to_poker_none(self):
        assert pt4_to_poker_pct(None) is None

    def test_pt4_to_poker_zero(self):
        assert pt4_to_poker_pct(0) is None

    def test_pt4_to_poker_allin(self):
        # 100% should return overflow value
        assert pt4_to_poker_pct(100) == 999.0

    def test_poker_to_pt4_roundtrip(self):
        # Test that conversion is reversible
        original = 33.33
        poker = pt4_to_poker_pct(original)
        back = poker_to_pt4_pct(poker)
        assert abs(back - original) < 0.1


class TestCardDecoding:
    def test_decode_ace_clubs(self):
        assert decode_card(1) == "Ac"

    def test_decode_ace_diamonds(self):
        assert decode_card(14) == "Ad"

    def test_decode_ace_hearts(self):
        assert decode_card(27) == "Ah"

    def test_decode_ace_spades(self):
        assert decode_card(40) == "As"

    def test_decode_king_spades(self):
        assert decode_card(52) == "Ks"

    def test_decode_ten_hearts(self):
        # Ten of hearts: rank 9 (0-indexed), suit 2
        # Card ID: 27 + 9 = 36
        assert decode_card(36) == "Th"

    def test_decode_none(self):
        assert decode_card(None) is None

    def test_decode_zero(self):
        assert decode_card(0) is None

    def test_decode_invalid(self):
        assert decode_card(53) is None
        assert decode_card(-1) is None


class TestBoardDecoding:
    def test_decode_flop(self):
        # Ac Kd 2h
        board = decode_board(1, 14, 28)
        assert board == "Ac Ad 2h"

    def test_decode_flop_turn(self):
        board = decode_board(1, 14, 27, 40)
        assert board == "Ac Ad Ah As"

    def test_decode_full_board(self):
        board = decode_board(1, 2, 3, 4, 5)
        assert board == "Ac 2c 3c 4c 5c"


class TestHoleCardDecoding:
    def test_decode_holdem(self):
        # Ah Kd
        cards = decode_hole_cards(27, 14)
        assert cards == "AhAd"

    def test_decode_omaha(self):
        # Ah Kd Qc Js
        cards = decode_hole_cards(27, 14, 12, 50)
        assert cards == "AhAdQcJs"


class TestActionParsing:
    def test_parse_bet(self):
        result = parse_action_string("B")
        assert result["first_action"] == "bet"
        assert result["villain_response"] is None

    def test_parse_check(self):
        result = parse_action_string("X")
        assert result["first_action"] == "check"

    def test_parse_bet_call(self):
        # Hero bet, villain raised, hero called
        result = parse_action_string("BC")
        assert result["first_action"] == "bet"
        assert result["villain_response"] == "raise"
        assert result["hero_response"] == "call"

    def test_parse_bet_fold(self):
        # Hero bet, villain raised, hero folded
        result = parse_action_string("BF")
        assert result["first_action"] == "bet"
        assert result["villain_response"] == "raise"
        assert result["hero_response"] == "fold"

    def test_parse_check_call(self):
        # Hero checked, villain bet, hero called
        result = parse_action_string("XC")
        assert result["first_action"] == "check"
        assert result["villain_response"] == "bet"
        assert result["hero_response"] == "call"

    def test_parse_none(self):
        result = parse_action_string(None)
        assert result["first_action"] is None


class TestBetSizeFormatting:
    def test_format_third_pot(self):
        result = format_bet_size(25)
        assert "33" in result
        assert "pot" in result

    def test_format_pot_sized(self):
        result = format_bet_size(50)
        assert "100" in result

    def test_format_with_pt4(self):
        result = format_bet_size(50, include_pt4=True)
        assert "100" in result
        assert "PT4: 50" in result

    def test_format_none(self):
        assert format_bet_size(None) == "N/A"

    def test_format_allin(self):
        assert format_bet_size(100) == "All-in"
