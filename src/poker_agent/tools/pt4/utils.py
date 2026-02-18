"""PT4 data parsing and conversion utilities."""

from typing import Any


def pt4_to_poker_pct(pt4_pct: float | None) -> float | None:
    """
    Convert PT4 FACING percentage format to poker percentage format.

    IMPORTANT: Only use this for FACING columns (villain's bets/raises):
    - val_f_bet_facing_pct, val_t_bet_facing_pct, val_r_bet_facing_pct
    - val_f_raise_facing_pct, etc.

    DO NOT use for MADE columns (hero's bets) - those are already in poker format!

    PT4 FACING format: bet / (pot + bet) * 100
    Poker format: bet / pot * 100

    Args:
        pt4_pct: Percentage in PT4 FACING format (0-100)

    Returns:
        Percentage in poker format, or None if invalid

    Examples:
        >>> pt4_to_poker_pct(25)  # 25% PT4 = 33% poker (1/3 pot)
        33.33...
        >>> pt4_to_poker_pct(50)  # 50% PT4 = 100% poker (pot-sized)
        100.0
    """
    if pt4_pct is None or pt4_pct <= 0:
        return None
    pct = pt4_pct / 100  # Convert to decimal
    if pct >= 1:
        return 999.0  # All-in or overflow
    poker_pct = pct / (1 - pct)
    return poker_pct * 100


def poker_to_pt4_pct(poker_pct: float | None) -> float | None:
    """
    Convert poker percentage format to PT4 percentage format.

    Inverse of pt4_to_poker_pct.

    Args:
        poker_pct: Percentage in poker format (e.g., 33 for 1/3 pot)

    Returns:
        Percentage in PT4 format
    """
    if poker_pct is None or poker_pct <= 0:
        return None
    pct = poker_pct / 100  # Convert to decimal
    pt4_pct = pct / (1 + pct)
    return pt4_pct * 100


def decode_card(card_id: int | None) -> str | None:
    """
    Convert PT4 card ID to readable format.

    PT4 encodes cards as 1-52 in suit-major order (13 cards per suit, 2-low):
    - 1-13: Clubs (2c, 3c, 4c, ..., Ac)
    - 14-26: Diamonds (2d, 3d, ..., Ad)
    - 27-39: Hearts (2h, 3h, ..., Ah)
    - 40-52: Spades (2s, 3s, ..., As)

    Args:
        card_id: PT4 card ID (1-52)

    Returns:
        Card string like "Ah" (Ace of hearts) or None

    Examples:
        >>> decode_card(1)
        '2c'
        >>> decode_card(13)
        'Ac'
        >>> decode_card(14)
        '2d'
        >>> decode_card(52)
        'As'
    """
    if card_id is None or card_id == 0:
        return None
    if card_id < 1 or card_id > 52:
        return None

    suits = ["c", "d", "h", "s"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]

    suit_idx = (card_id - 1) // 13
    rank_idx = (card_id - 1) % 13

    return ranks[rank_idx] + suits[suit_idx]


def decode_board(
    card_1: int | None,
    card_2: int | None,
    card_3: int | None,
    card_4: int | None = None,
    card_5: int | None = None,
) -> str:
    """
    Decode PT4 board cards to readable format.

    Args:
        card_1, card_2, card_3: Flop cards
        card_4: Turn card (optional)
        card_5: River card (optional)

    Returns:
        Board string like "Ah Kd 2c" or "Ah Kd 2c Ts 5h"
    """
    cards = []
    for card_id in [card_1, card_2, card_3]:
        decoded = decode_card(card_id)
        if decoded:
            cards.append(decoded)

    if card_4:
        decoded = decode_card(card_4)
        if decoded:
            cards.append(decoded)

    if card_5:
        decoded = decode_card(card_5)
        if decoded:
            cards.append(decoded)

    return " ".join(cards)


def decode_hole_cards(
    holecard_1: int | None,
    holecard_2: int | None,
    holecard_3: int | None = None,
    holecard_4: int | None = None,
) -> str:
    """
    Decode PT4 hole cards to readable format.

    Args:
        holecard_1, holecard_2: Hold'em hole cards
        holecard_3, holecard_4: Additional Omaha cards (optional)

    Returns:
        Hole cards string like "AhKd" or "AhKdQcJs" for Omaha
    """
    cards = []
    for card_id in [holecard_1, holecard_2, holecard_3, holecard_4]:
        if card_id:
            decoded = decode_card(card_id)
            if decoded:
                cards.append(decoded)
    return "".join(cards)


def parse_action_string(action: str | None) -> dict[str, Any]:
    """
    Parse PT4 action string into structured format.

    Args:
        action: PT4 action string like "B", "BC", "XC", etc.

    Returns:
        Dict with parsed action info:
        - first_action: What hero did first (bet, check, call, fold, raise)
        - villain_response: What villain did (if applicable)
        - hero_response: What hero did after villain (if applicable)
    """
    if not action:
        return {"first_action": None, "villain_response": None, "hero_response": None}

    action_map = {
        "B": "bet",
        "X": "check",
        "C": "call",
        "F": "fold",
        "R": "raise",
    }

    result = {
        "first_action": action_map.get(action[0]),
        "villain_response": None,
        "hero_response": None,
        "raw": action,
    }

    if len(action) >= 2:
        # Hero did something, villain responded, hero responded
        # e.g., BC = bet, villain raised, hero called
        if action[0] == "B":
            result["villain_response"] = "raise"  # Villain raised hero's bet
            result["hero_response"] = action_map.get(action[1])
        elif action[0] == "X":
            result["villain_response"] = "bet"  # Villain bet after hero checked
            result["hero_response"] = action_map.get(action[1])
        elif action[0] == "C":
            # Called then something happened
            if len(action) >= 2:
                result["hero_response"] = action_map.get(action[1])

    return result


def format_bet_size(
    pt4_pct: float | None, include_pt4: bool = False
) -> str:
    """
    Format a bet size for display.

    Args:
        pt4_pct: Bet size in PT4 percentage format
        include_pt4: Whether to include PT4 format in output

    Returns:
        Formatted string like "33% pot" or "33% pot (PT4: 25%)"
    """
    if pt4_pct is None:
        return "N/A"

    poker_pct = pt4_to_poker_pct(pt4_pct)
    if poker_pct is None:
        return "N/A"

    if poker_pct >= 999:
        return "All-in"

    if include_pt4:
        return f"{poker_pct:.0f}% pot (PT4: {pt4_pct:.0f}%)"
    return f"{poker_pct:.0f}% pot"
