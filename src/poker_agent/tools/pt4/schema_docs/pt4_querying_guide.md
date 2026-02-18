# PokerTracker 4 Database Querying Guide

## Critical: PT4 Percentage Formats

**PT4 uses DIFFERENT formats for MADE vs FACING percentages!**

### MADE Percentages (Hero's bets) - NO CONVERSION NEEDED

Columns like `val_f_bet_made_pct` store hero's bet sizes in **poker format**:
```
bet_made_pct = bet / pot * 100
```
A 33% value means a 33% pot bet. Use these values directly.

### FACING Percentages (Villain's bets) - CONVERSION REQUIRED

Columns like `val_f_bet_facing_pct` store villain's bet sizes in **PT4 format**:
```
pt4_pct = bet / (pot + bet) * 100
```
A 25% value here actually means a 33% pot bet!

### Conversion Formula (for FACING percentages only)

```python
def pt4_to_poker_pct(pt4_pct):
    """Convert PT4 FACING percentage to poker percentage."""
    if pt4_pct is None or pt4_pct <= 0:
        return 0
    pct = pt4_pct / 100  # Convert to decimal
    if pct >= 1:
        return 999  # All-in or invalid
    poker_pct = pct / (1 - pct)
    return poker_pct * 100

# Examples for FACING percentages:
# PT4 25% → Poker 33% (1/3 pot)
# PT4 33% → Poker 50% (1/2 pot)
# PT4 50% → Poker 100% (pot-sized)
# PT4 75% → Poker 300% (3x pot)
```

### PT4 → Poker Conversions (for FACING columns only)

| PT4 FACING % | Poker % | Description |
|--------------|---------|-------------|
| 20%          | 25%     | Quarter pot |
| 25%          | 33%     | Third pot |
| 33%          | 50%     | Half pot |
| 40%          | 67%     | Two-thirds pot |
| 50%          | 100%    | Pot-sized |
| 60%          | 150%    | 1.5x pot |
| 75%          | 300%    | 3x pot |

### Raise Percentages - More Complex

**Raise MADE** (`val_f_raise_made_pct`): Uses `raise_to / (pot + bet)` format
**Raise FACING** (`val_f_raise_facing_pct`): Uses `raise_to / (raise_to + pot + 2*bet)` format

Both need special conversion to get the raise SIZE (not raise-to amount).

---

## Core Tables

### cash_hand_player_statistics (chps)
Per-player statistics for each hand. Main table for analysis.

Key columns:
- `id_hand` - Hand identifier
- `id_player` - Player identifier
- `id_limit` - Stakes/limit identifier
- `id_gametype` - Game type (1 = Hold'em, 2 = Omaha)
- `holecard_1`, `holecard_2`, `holecard_3`, `holecard_4` - Hole cards as numeric IDs
- `position` - Seat position
- `flg_f_has_position` - Boolean: has position on flop
- `amt_won` - Amount won/lost in hand

**Action flags** (per street):
- `flg_f_saw`, `flg_t_saw`, `flg_r_saw` - Saw this street
- `flg_f_bet`, `flg_t_bet`, `flg_r_bet` - Made a bet
- `flg_f_raise`, `flg_t_raise`, `flg_r_raise` - Made a raise
- `flg_f_cbet`, `flg_t_cbet`, `flg_r_cbet` - Made continuation bet
- `flg_f_cbet_opp`, `flg_t_cbet_opp`, `flg_r_cbet_opp` - Had cbet opportunity
- `flg_f_fold`, `flg_t_fold`, `flg_r_fold` - Folded

**Bet sizing**:
- `val_f_bet_made_pct`, `val_t_bet_made_pct`, `val_r_bet_made_pct` - Hero's bet size (poker format, no conversion)
- `val_f_bet_facing_pct`, `val_t_bet_facing_pct`, `val_r_bet_facing_pct` - Villain's bet size (PT4 format, MUST CONVERT)
- `val_f_raise_made_pct`, `val_t_raise_made_pct`, `val_r_raise_made_pct` - Hero's raise size (complex format)
- `val_f_raise_facing_pct`, `val_t_raise_facing_pct`, `val_r_raise_facing_pct` - Villain's raise size (complex format)
- `val_f_raise_facing_pct`, `val_t_raise_facing_pct`, `val_r_raise_facing_pct` - Villain's raise

**Action IDs** (join to lookup_actions):
- `id_action_f`, `id_action_t`, `id_action_r`, `id_action_p` - Action codes per street

### cash_hand_summary (chs)
One row per hand with summary information.

Key columns:
- `id_hand` - Hand identifier
- `id_limit` - Stakes identifier
- `hand_no` - Hand number from site
- `id_site` - Poker site ID
- `date_played` - When hand was played
- `cnt_players` - Number of players dealt in
- `id_winner` - Winner's player ID
- `amt_pot` - Final pot size
- `card_1`, `card_2`, `card_3` - Flop cards
- `card_4` - Turn card
- `card_5` - River card
- `str_aggressors_p` - Preflop aggressor positions (length indicates bet level)
- `str_actors_p` - Preflop actors order

### player
Player information.

Key columns:
- `id_player` - Player identifier
- `player_name` - Display name
- `player_name_search` - Lowercase searchable name
- `id_site` - Site ID

### lookup_actions
Decodes action IDs to action strings.

- `id_action` - Action identifier
- `action` - Action string (e.g., "B", "XC", "BR")

---

## Action String Format

PT4 encodes player actions as compact strings:

### Single Characters
- `B` - Bet (first aggression)
- `X` - Check
- `C` - Call
- `F` - Fold
- `R` - Raise

### Multi-Character Sequences
The string shows hero's actions and implied villain responses:
- `BC` - Hero bet, villain raised, hero called
- `BR` - Hero bet, villain raised, hero re-raised
- `BF` - Hero bet, villain raised, hero folded
- `XC` - Hero checked, villain bet, hero called
- `XF` - Hero checked, villain bet, hero folded
- `XB` - Hero checked, villain bet (then hero raised - check-raise)
- `CC` - Both checked (or hero called a bet)

### Parsing Logic
```python
action = hand.get("action_f")  # Flop action string

if action == 'B':
    # Hero bet, villain called or folded
    # Check next street to determine outcome
    if hand.get("flg_t_saw"):
        # Villain called, saw turn
    else:
        # Villain folded

elif action.startswith('B') and len(action) > 1:
    # Hero bet, villain raised
    # Second char is hero's response: C=call, R=reraise, F=fold

elif action == 'X':
    # Hero checked (may have been checked through or villain bet)

elif action.startswith('X') and len(action) > 1:
    # Hero checked, villain bet, hero responded
```

---

## Common Query Patterns

### Basic Player Lookup
```sql
SELECT id_player, player_name, id_site
FROM player
WHERE player_name_search = lower('PlayerName')
  AND id_site = 5600;  -- CoinPoker
```

### SRP Heads-Up Hands (Single Raised Pot, 2 players)
```sql
SELECT
    chs.id_hand,
    chps.holecard_1, chps.holecard_2,
    chs.card_1, chs.card_2, chs.card_3,  -- flop
    chs.card_4,  -- turn
    chs.card_5,  -- river
    la_f.action as action_f,
    la_t.action as action_t,
    la_r.action as action_r
FROM cash_hand_player_statistics chps
JOIN cash_hand_summary chs
    ON chs.id_hand = chps.id_hand AND chs.id_limit = chps.id_limit
LEFT JOIN lookup_actions la_f ON la_f.id_action = chps.id_action_f
LEFT JOIN lookup_actions la_t ON la_t.id_action = chps.id_action_t
LEFT JOIN lookup_actions la_r ON la_r.id_action = chps.id_action_r
WHERE chps.id_player = (SELECT id_player FROM player WHERE player_name_search = 'playername')
  AND chps.id_gametype = 1  -- Hold'em
  AND chs.cnt_players = 2   -- Heads-up
  AND length(chs.str_aggressors_p) = 2;  -- Single raised pot
```

### Flop Cbet Analysis (Hero IP with cbet opportunity)
```sql
SELECT
    chps.id_hand,
    chps.flg_f_cbet,
    chps.val_f_bet_made_pct as bet_pct_pt4,
    la_f.action as action_f
FROM cash_hand_player_statistics chps
JOIN cash_hand_summary chs
    ON chs.id_hand = chps.id_hand AND chs.id_limit = chps.id_limit
LEFT JOIN lookup_actions la_f ON la_f.id_action = chps.id_action_f
WHERE chps.id_player = ?
  AND chps.flg_f_cbet_opp = true
  AND chps.flg_f_has_position = true;
```

### Bet Size Distribution
```sql
SELECT
    ROUND(val_f_bet_made_pct) as pt4_pct,
    COUNT(*) as count
FROM cash_hand_player_statistics
WHERE id_player = ?
  AND flg_f_bet = true
  AND val_f_bet_made_pct IS NOT NULL
GROUP BY ROUND(val_f_bet_made_pct)
ORDER BY pt4_pct;
```

---

## Site ID Reference

| Site ID | Site Name |
|---------|-----------|
| 100     | PokerStars |
| 200     | Full Tilt |
| 300     | PartyPoker |
| 500     | 888poker |
| 3600    | RedDragon |
| 5600    | CoinPoker |

---

## Card ID Encoding

PT4 stores cards as numeric IDs (1-52):
- Cards 1-13: Clubs (A, 2, 3, ..., K)
- Cards 14-26: Diamonds
- Cards 27-39: Hearts
- Cards 40-52: Spades

To decode:
```python
def decode_card(card_id):
    """Convert PT4 card ID to readable format."""
    if card_id is None or card_id == 0:
        return None
    suits = ['c', 'd', 'h', 's']
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
    suit_idx = (card_id - 1) // 13
    rank_idx = (card_id - 1) % 13
    return ranks[rank_idx] + suits[suit_idx]

# Examples:
# 1 → Ac (Ace of clubs)
# 14 → Ad (Ace of diamonds)
# 52 → Ks (King of spades)
```

---

## Tips for Accurate Queries

1. **Always convert percentages** - Use `pt4_to_poker_pct()` when displaying bet sizes
2. **Join with id_limit** - When joining chps to chs, include both `id_hand` AND `id_limit`
3. **Use player_name_search** - It's lowercase and indexed for fast lookups
4. **Check SRP with str_aggressors_p** - Length 2 = single raise, length 4 = 3bet pot
5. **Filter by id_gametype** - 1 = Hold'em, 2 = Omaha
6. **Date filtering** - Use `date_played` on cash_hand_summary, not player_statistics
