"""Live CLI walkthrough: for each persona, replay their scripted transaction
scenario and print the mem0 lookup latency + decision for each one."""

import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "data" / "personas"))

from personas import PERSONAS  # noqa: E402

from txmonitor.core.memory_client import build_memory  # noqa: E402
from txmonitor.core.processor import process_transaction  # noqa: E402
from txmonitor.core.retry import with_rate_limit_retry  # noqa: E402
from txmonitor.core.rules import Transaction  # noqa: E402

console = Console()


def run():
    load_dotenv()
    console.print("[bold]Connecting to mem0 (ScyllaDB + Gemini + HuggingFace)...[/bold]")
    memory = build_memory()

    for persona in PERSONAS:
        user_id = persona["user_id"]
        console.rule(f"[bold cyan]{user_id}[/bold cyan]")

        for step in persona["scenario"]:
            transaction = Transaction(
                user_id=user_id,
                amount=step["amount"],
                location=step["location"],
                merchant_category=step["merchant_category"],
                description=step["description"],
            )

            result = process_transaction(
                memory,
                transaction,
                known_locations_seed=persona["known_locations"],
                known_categories_seed=persona["known_categories"],
            )

            header = (
                f"[bold]{transaction.description}[/bold]  "
                f"${transaction.amount:.2f} @ {transaction.location} ({transaction.merchant_category})"
            )
            body_lines = [f"mem0 lookup latency: [yellow]{result.lookup_latency_ms:.1f} ms[/yellow]"]
            body_lines.append(f"recalled {len(result.recalled_facts)} facts")

            if result.decision.flagged:
                verdict = "[bold red]FLAGGED[/bold red]"
                body_lines.append("reasons:")
                body_lines.extend(f"  - {reason}" for reason in result.decision.reasons)
            else:
                verdict = "[bold green]APPROVED[/bold green]"

            body_lines.insert(0, f"decision: {verdict}")

            console.print(Panel("\n".join(body_lines), title=header, expand=False))

            # Feed the outcome back into memory so subsequent lookups see it,
            # same as a real system would record the transaction it just judged.
            with_rate_limit_retry(
                memory.add,
                f"Made a purchase of ${transaction.amount:.2f} at {transaction.location} "
                f"({transaction.merchant_category}): {transaction.description}."
                + (" This was flagged as unusual." if result.decision.flagged else ""),
                user_id=user_id,
            )

    console.print("\n[bold green]Scenario complete.[/bold green]")


if __name__ == "__main__":
    run()
