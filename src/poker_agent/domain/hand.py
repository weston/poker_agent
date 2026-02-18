"""Hand parsing and evaluation utilities."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Suit(Enum):
    """Card suits."""

    CLUBS = "c"
    DIAMONDS = "d"
    HEARTS = "h"
    SPADES = "s"

    @classmethod
    def from_char(cls, char: str) -> "Suit":
        """Parse suit from character."""
        char = char.lower()
        for suit in cls:
            if suit.value == char:
                return suit
        raise ValueError(f"Invalid suit character: {char}")


class Rank(Enum):
    """Card ranks."""

    TWO = ("2", 2)
    THREE = ("3", 3)
    FOUR = ("4", 4)
    FIVE = ("5", 5)
    SIX = ("6", 6)
    SEVEN = ("7", 7)
    EIGHT = ("8", 8)
    NINE = ("9", 9)
    TEN = ("T", 10)
    JACK = ("J", 11)
    QUEEN = ("Q", 12)
    KING = ("K", 13)
    ACE = ("A", 14)

    def __init__(self, char: str, value: int):
        self.char = char
        self.numeric_value = value

    @classmethod
    def from_char(cls, char: str) -> "Rank":
        """Parse rank from character."""
        char = char.upper()
        for rank in cls:
            if rank.char == char:
                return rank
        raise ValueError(f"Invalid rank character: {char}")


@dataclass
class Card:
    """A single playing card."""

    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank.char}{self.suit.value}"

    @classmethod
    def parse(cls, s: str) -> "Card":
        """Parse a card from string like 'Ah' or 'Ts'."""
        if len(s) != 2:
            raise ValueError(f"Invalid card string: {s}")
        return cls(rank=Rank.from_char(s[0]), suit=Suit.from_char(s[1]))


@dataclass
class Hand:
    """A poker hand (hole cards)."""

    card1: Card
    card2: Card

    def __str__(self) -> str:
        return f"{self.card1}{self.card2}"

    @property
    def is_pair(self) -> bool:
        """Check if hand is a pocket pair."""
        return self.card1.rank == self.card2.rank

    @property
    def is_suited(self) -> bool:
        """Check if hand is suited."""
        return self.card1.suit == self.card2.suit

    @property
    def short_notation(self) -> str:
        """Get short notation like 'AKs' or 'QQ'."""
        # Put higher rank first
        if self.card1.rank.numeric_value >= self.card2.rank.numeric_value:
            r1, r2 = self.card1.rank.char, self.card2.rank.char
        else:
            r1, r2 = self.card2.rank.char, self.card1.rank.char

        if self.is_pair:
            return f"{r1}{r2}"
        elif self.is_suited:
            return f"{r1}{r2}s"
        else:
            return f"{r1}{r2}o"

    @classmethod
    def parse(cls, s: str) -> "Hand":
        """
        Parse a hand from string.

        Accepts formats like:
        - 'AhKh' (full notation)
        - 'Ah Kh' (with space)
        - 'AKs' (short notation - returns representative hand)
        - 'AKo' (short offsuit)
        - 'QQ' (pocket pair)
        """
        s = s.strip().replace(" ", "")

        # Full notation (4 chars)
        if len(s) == 4:
            return cls(card1=Card.parse(s[:2]), card2=Card.parse(s[2:]))

        # Short notation
        if len(s) in (2, 3):
            r1 = Rank.from_char(s[0])
            r2 = Rank.from_char(s[1])

            suited = len(s) == 3 and s[2].lower() == "s"

            if suited:
                return cls(
                    card1=Card(r1, Suit.SPADES), card2=Card(r2, Suit.SPADES)
                )
            else:
                return cls(
                    card1=Card(r1, Suit.SPADES), card2=Card(r2, Suit.HEARTS)
                )

        raise ValueError(f"Invalid hand string: {s}")


def parse_hand(s: str) -> Hand:
    """Parse a hand string into a Hand object."""
    return Hand.parse(s)


def parse_board(s: str) -> list[Card]:
    """
    Parse a board string into list of cards.

    Accepts formats like:
    - 'Ah Kd 2c'
    - 'AhKd2c'
    - 'Ah Kd 2c Ts 5h'
    """
    s = s.strip()

    # Try to split by spaces first
    if " " in s:
        parts = s.split()
    else:
        # Split every 2 characters
        parts = [s[i : i + 2] for i in range(0, len(s), 2)]

    return [Card.parse(p) for p in parts if p]
