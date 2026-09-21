"""Pre-loads each persona's behavioral history into mem0, before the live demo starts."""

import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "data" / "personas"))

from personas import PERSONAS  # noqa: E402

from txmonitor.core.memory_client import build_memory  # noqa: E402
from txmonitor.core.retry import with_rate_limit_retry  # noqa: E402

console = Console()

# Gemini's free tier caps requests-per-minute (not just tokens), so a short
# delay keeps back-to-back mem0.add() calls comfortably under that ceiling.
SEED_DELAY_SECONDS = 5


def seed():
    load_dotenv()
    console.print("[bold]Connecting to mem0 (ScyllaDB + Gemini + HuggingFace)...[/bold]")
    memory = build_memory()

    for persona in PERSONAS:
        user_id = persona["user_id"]
        console.print(f"\n[bold cyan]Seeding {user_id}[/bold cyan] ({len(persona['history'])} facts)")
        for fact in persona["history"]:
            with_rate_limit_retry(memory.add, fact, user_id=user_id)
            console.print(f"  [dim]added:[/dim] {fact}")
            time.sleep(SEED_DELAY_SECONDS)

    console.print("\n[bold green]Done seeding all personas.[/bold green]")


if __name__ == "__main__":
    seed()
