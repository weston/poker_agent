# Poker AI Agent

A CLI-based conversational AI agent for professional poker players that can query PokerTracker 4 data, run analysis, and assist with strategic research.

## Features

- **LLM-powered conversations** - Uses OpenAI or Anthropic models for natural language interaction
- **PokerTracker 4 integration** - Query your PT4 PostgreSQL database for player stats and hand histories
- **Statistical analysis** - EV calculations and poker math assistance
- **User profiles** - Store your custom definitions, instructions, and preferences

## Installation

### Quick Install (Windows)

```cmd
install.bat
```

### Quick Install (Linux/Mac)

```bash
chmod +x install.sh
./install.sh
```

### Manual Installation

```bash
# Clone or download the project
cd poker_agent

# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your settings:
   ```
   # Choose your LLM provider
   LLM_PROVIDER=anthropic  # or "openai"

   # API Keys (set the one you're using)
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...

   # PT4 Database (optional - for database queries)
   PT4_DB_HOST=localhost
   PT4_DB_PORT=5432
   PT4_DB_NAME=pt4_db
   PT4_DB_USER=postgres
   PT4_DB_PASSWORD=your_password
   ```

## Usage

Start the agent:

```bash
python -m poker_agent
# or
poker-agent
```

### Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/profile` | View your profile |
| `/profile set context <text>` | Set your player context |
| `/profile set name <name>` | Set your screen name |
| `/profile add def <term> = <definition>` | Add custom definition |
| `/profile add instruction <text>` | Add custom instruction |
| `/profile remove def <term>` | Remove a definition |
| `/profile remove instruction <n>` | Remove instruction by number |
| `/clear` | Clear conversation history |
| `/quit` | Exit the agent |

### Example Conversation

```
[You] > What are villain's stats at my table?

[Using tool: get_player_stats]

Based on the PT4 data, villain123 has played 2,847 hands with:
- VPIP: 28.3%
- PFR: 21.7%
- 3-Bet: 8.2%

This profile suggests a loose-aggressive (LAG) player...
```

### Custom Profile

Set up your profile for personalized assistance:

```
/profile set name YourPokerName
/profile set context I play NL200 6-max zoom on PokerStars. I focus on GTO with exploitative adjustments.
/profile add def Fish = Recreational player with VPIP > 40%
/profile add instruction Always express win rates in BB/100
```

## Project Structure

```
poker_agent/
├── src/poker_agent/
│   ├── agent/          # Agent orchestration
│   ├── config/         # Settings management
│   ├── domain/         # Poker domain logic
│   ├── llm/            # LLM provider abstraction
│   └── tools/          # Tool implementations
└── tests/              # Test suite
```

## Development

Run tests:

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
