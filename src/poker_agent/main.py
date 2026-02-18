"""CLI entry point for the poker agent."""

import asyncio
import sys
from pathlib import Path

# Fix for Windows event loop compatibility with psycopg async
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agent import AgentOrchestrator
from .config import get_settings
from .domain.user_profile import (
    UserProfile,
    get_default_profile_path,
    load_user_profile,
    save_user_profile,
)
from .llm import get_provider
from .tools import registry

# Import tools to register them
from .tools.pt4 import queries as _  # noqa: F401
from .tools.pt4 import schema_search as _schema  # noqa: F401
from .tools.analysis import stats as _  # noqa: F401

console = Console()


def print_welcome():
    """Print welcome message."""
    console.print(
        Panel(
            "[bold blue]Poker AI Agent[/bold blue]\n"
            "Your AI assistant for poker analysis and research.\n\n"
            "Commands:\n"
            "  [green]/help[/green]     - Show available commands\n"
            "  [green]/profile[/green]  - View/edit your profile\n"
            "  [green]/clear[/green]    - Clear conversation history\n"
            "  [green]/quit[/green]     - Exit the agent",
            title="Welcome",
            border_style="blue",
        )
    )


def print_help():
    """Print help information."""
    console.print(
        Panel(
            "[bold]Available Commands[/bold]\n\n"
            "[green]/help[/green]\n"
            "  Show this help message\n\n"
            "[green]/profile[/green]\n"
            "  View your current profile settings\n\n"
            "[green]/profile set context <text>[/green]\n"
            "  Set your player context (stakes, games, style)\n\n"
            "[green]/profile set name <name>[/green]\n"
            "  Set your player screen name\n\n"
            "[green]/profile add def <term> = <definition>[/green]\n"
            "  Add a custom definition\n\n"
            "[green]/profile add instruction <text>[/green]\n"
            "  Add a custom instruction for the agent\n\n"
            "[green]/profile remove def <term>[/green]\n"
            "  Remove a custom definition\n\n"
            "[green]/profile remove instruction <number>[/green]\n"
            "  Remove an instruction by its number\n\n"
            "[green]/clear[/green]\n"
            "  Clear conversation history\n\n"
            "[green]/quit[/green] or [green]/exit[/green]\n"
            "  Exit the agent",
            title="Help",
            border_style="green",
        )
    )


def print_profile(profile: UserProfile):
    """Print current profile."""
    lines = []

    if profile.player_name:
        lines.append(f"[bold]Player Name:[/bold] {profile.player_name}")
    else:
        lines.append("[bold]Player Name:[/bold] [dim]Not set[/dim]")

    if profile.context:
        lines.append(f"\n[bold]Context:[/bold]\n{profile.context}")
    else:
        lines.append("\n[bold]Context:[/bold] [dim]Not set[/dim]")

    if profile.definitions:
        lines.append("\n[bold]Custom Definitions:[/bold]")
        for term, defn in profile.definitions.items():
            lines.append(f"  • {term}: {defn}")
    else:
        lines.append("\n[bold]Custom Definitions:[/bold] [dim]None[/dim]")

    if profile.instructions:
        lines.append("\n[bold]Custom Instructions:[/bold]")
        for i, inst in enumerate(profile.instructions, 1):
            lines.append(f"  {i}. {inst}")
    else:
        lines.append("\n[bold]Custom Instructions:[/bold] [dim]None[/dim]")

    if profile.preferred_games:
        lines.append(f"\n[bold]Preferred Games:[/bold] {', '.join(profile.preferred_games)}")

    console.print(
        Panel(
            "\n".join(lines),
            title="Your Profile",
            border_style="cyan",
        )
    )


def handle_profile_command(
    args: list[str], profile: UserProfile, orchestrator: AgentOrchestrator
) -> UserProfile:
    """Handle profile commands."""
    if not args:
        print_profile(profile)
        return profile

    cmd = args[0].lower()

    if cmd == "set":
        if len(args) < 3:
            console.print("[red]Usage: /profile set <field> <value>[/red]")
            return profile

        field = args[1].lower()
        value = " ".join(args[2:])

        if field == "context":
            profile.context = value
            console.print(f"[green]Context updated.[/green]")
        elif field == "name":
            profile.player_name = value
            console.print(f"[green]Player name set to: {value}[/green]")
        else:
            console.print(f"[red]Unknown field: {field}[/red]")
            return profile

    elif cmd == "add":
        if len(args) < 3:
            console.print("[red]Usage: /profile add <def|instruction> <value>[/red]")
            return profile

        subcmd = args[1].lower()

        if subcmd == "def":
            # Parse "term = definition"
            rest = " ".join(args[2:])
            if "=" not in rest:
                console.print("[red]Usage: /profile add def <term> = <definition>[/red]")
                return profile
            term, defn = rest.split("=", 1)
            profile.add_definition(term.strip(), defn.strip())
            console.print(f"[green]Definition added: {term.strip()}[/green]")

        elif subcmd == "instruction":
            instruction = " ".join(args[2:])
            profile.add_instruction(instruction)
            console.print("[green]Instruction added.[/green]")

        else:
            console.print(f"[red]Unknown: {subcmd}. Use 'def' or 'instruction'[/red]")
            return profile

    elif cmd == "remove":
        if len(args) < 3:
            console.print("[red]Usage: /profile remove <def|instruction> <term|number>[/red]")
            return profile

        subcmd = args[1].lower()

        if subcmd == "def":
            term = " ".join(args[2:])
            if profile.remove_definition(term):
                console.print(f"[green]Definition removed: {term}[/green]")
            else:
                console.print(f"[yellow]Definition not found: {term}[/yellow]")

        elif subcmd == "instruction":
            try:
                num = int(args[2]) - 1
                if 0 <= num < len(profile.instructions):
                    removed = profile.instructions.pop(num)
                    console.print(f"[green]Instruction removed: {removed}[/green]")
                else:
                    console.print("[red]Invalid instruction number[/red]")
            except ValueError:
                console.print("[red]Please provide instruction number[/red]")
            return profile

        else:
            console.print(f"[red]Unknown: {subcmd}. Use 'def' or 'instruction'[/red]")
            return profile

    else:
        print_profile(profile)
        return profile

    # Save profile and update orchestrator
    save_user_profile(profile)
    orchestrator.update_user_profile(profile)
    return profile


async def main_loop():
    """Main conversation loop."""
    settings = get_settings()

    # Load user profile
    profile = load_user_profile()

    # Initialize LLM provider
    try:
        llm = get_provider()
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        console.print(
            "\nPlease set up your .env file with API keys. "
            "See .env.example for reference."
        )
        return

    # Create orchestrator
    orchestrator = AgentOrchestrator(
        llm=llm,
        tools=registry,
        user_profile=profile,
    )

    # Set up prompt session with history
    history_path = Path.home() / ".poker_agent" / "history.txt"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    session: PromptSession = PromptSession(history=FileHistory(str(history_path)))

    print_welcome()

    while True:
        try:
            # Get user input
            user_input = await session.prompt_async("\n[You] > ")
            user_input = user_input.strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                parts = user_input[1:].split()
                cmd = parts[0].lower() if parts else ""
                args = parts[1:] if len(parts) > 1 else []

                if cmd in ("quit", "exit", "q"):
                    console.print("[dim]Goodbye![/dim]")
                    break
                elif cmd == "help":
                    print_help()
                elif cmd == "clear":
                    orchestrator.clear_history()
                    console.print("[green]Conversation history cleared.[/green]")
                elif cmd == "profile":
                    profile = handle_profile_command(args, profile, orchestrator)
                else:
                    console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
                continue

            # Process message
            console.print()
            response_text = []

            async for chunk in orchestrator.process_message(user_input):
                if chunk.startswith("\n[Using tool:"):
                    console.print(f"[dim]{chunk.strip()}[/dim]")
                else:
                    response_text.append(chunk)

            # Display response as markdown
            if response_text:
                full_response = "".join(response_text)
                console.print(Markdown(full_response))

        except KeyboardInterrupt:
            console.print("\n[dim]Use /quit to exit[/dim]")
        except EOFError:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    """Entry point."""
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
