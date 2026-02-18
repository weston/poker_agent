"""PT4 database schema documentation.

This module documents the key tables and columns in the PokerTracker 4 database
for reference when building queries.
"""

PT4_SCHEMA_INFO = """
# PokerTracker 4 Database Schema Reference

## Key Tables

### player
- id_player: Primary key
- player_name: Screen name
- id_site: Poker site ID

### cash_hand_player_statistics
Main table for cash game hand data.

Key columns:
- id_hand: Hand reference
- id_player: Player reference
- amt_won: Amount won/lost in hand
- flg_vpip: Voluntarily put money in pot
- flg_p_raise: Preflop raise
- flg_p_3bet: Made a 3-bet preflop
- flg_p_3bet_opp: Had opportunity to 3-bet
- flg_p_fold_to_3bet: Folded to 3-bet
- flg_p_face_3bet: Faced a 3-bet
- flg_c_bet: Made continuation bet
- flg_c_bet_opp: Had c-bet opportunity
- val_p_raise_aggressor_pos: Position of raiser
- cnt_p_call: Number of preflop calls
- amt_p_raise_made: Preflop raise amount
- amt_blind: Blind amount
- id_limit: Limit/stakes reference

### tournament_hand_player_statistics
Similar structure to cash_hand_player_statistics but for tournament hands.

### cash_hand_summary
- id_hand: Primary key
- date_played: When hand was played
- amt_pot: Final pot size
- id_table: Table reference
- cnt_players: Number of players

### lookup_actions
- id_action: Action ID
- action: Action name (fold, call, raise, etc.)

## Common Stat Calculations

VPIP = hands where flg_vpip = true / total hands
PFR = hands where flg_p_raise = true / total hands
3-Bet% = hands where flg_p_3bet = true / hands where flg_p_3bet_opp = true
C-Bet% = hands where flg_c_bet = true / hands where flg_c_bet_opp = true
"""


def get_schema_reference() -> str:
    """Get the PT4 schema reference documentation."""
    return PT4_SCHEMA_INFO
