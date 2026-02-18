"""Tests for hand parsing."""

import pytest

from poker_agent.domain.hand import Card, Hand, Rank, Suit, parse_hand, parse_board


class TestCard:
    def test_parse_valid(self):
        card = Card.parse("Ah")
        assert card.rank == Rank.ACE
        assert card.suit == Suit.HEARTS

    def test_parse_lowercase(self):
        card = Card.parse("ts")
        assert card.rank == Rank.TEN
        assert card.suit == Suit.SPADES

    def test_str(self):
        card = Card(Rank.KING, Suit.DIAMONDS)
        assert str(card) == "Kd"


class TestHand:
    def test_parse_full_notation(self):
        hand = parse_hand("AhKh")
        assert hand.card1.rank == Rank.ACE
        assert hand.card2.rank == Rank.KING
        assert hand.is_suited

    def test_parse_with_space(self):
        hand = parse_hand("Ah Kh")
        assert hand.is_suited

    def test_parse_short_suited(self):
        hand = parse_hand("AKs")
        assert hand.is_suited
        assert hand.card1.rank == Rank.ACE
        assert hand.card2.rank == Rank.KING

    def test_parse_short_offsuit(self):
        hand = parse_hand("AKo")
        assert not hand.is_suited

    def test_parse_pair(self):
        hand = parse_hand("QQ")
        assert hand.is_pair
        assert hand.card1.rank == Rank.QUEEN
        assert hand.card2.rank == Rank.QUEEN

    def test_short_notation_suited(self):
        hand = parse_hand("JTs")
        assert hand.short_notation == "JTs"

    def test_short_notation_pair(self):
        hand = parse_hand("AA")
        assert hand.short_notation == "AA"


class TestBoard:
    def test_parse_with_spaces(self):
        board = parse_board("Ah Kd 2c")
        assert len(board) == 3
        assert board[0].rank == Rank.ACE

    def test_parse_no_spaces(self):
        board = parse_board("AhKd2c")
        assert len(board) == 3

    def test_parse_full_board(self):
        board = parse_board("Ah Kd 2c Ts 5h")
        assert len(board) == 5
