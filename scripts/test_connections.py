"""
scripts/test_connections.py
────────────────────────────
Run this first after setup to verify all connections are healthy.

Usage (from crm-ai-followup/ root):
    python scripts/test_connections.py

Expected output:
    ✅ PostgreSQL OK
    ✅ Pinecone OK   (only after you add PINECONE_API_KEY to .env)
    ❌ Pinecone FAILED: PINECONE_API_KEY is not set  (before setup)
"""
import sys
import os
# Make sure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vector.pinecone_client import test_pinecone_connection
from src.db.connection import test_connection as test_postgres


# Make sure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("Error: 'rich' package is not installed. Please run: pip install rich")
    sys.exit(1)


console = Console()


def run_checks():
    console.rule("[bold blue]AI CRM Follow-Up — Connection Check")

    results = []

    # ── 1. PostgreSQL ──────────────────────────────────────────
    console.print("\n[yellow]Testing PostgreSQL connection...[/yellow]")
    try:
        pg_ok = test_postgres()
        results.append(("PostgreSQL", pg_ok, "dea_analytics_dev @ sales_raw"))
    except Exception as e:
        results.append(("PostgreSQL", False, str(e)))

    # ── 2. Pinecone ────────────────────────────────────────────
    console.print("\n[yellow]Testing Pinecone connection...[/yellow]")
    try:
        pc_ok = test_pinecone_connection()
        results.append(("Pinecone Serverless", pc_ok,
                       "crm-nurture-content + crm-testimonials"))
    except ValueError as e:
        results.append(("Pinecone Serverless", False, str(e)))
    except Exception as e:
        results.append(("Pinecone Serverless", False, str(e)))

    # ── Summary table ──────────────────────────────────────────
    console.print()
    table = Table(title="Connection Results", show_lines=True)
    table.add_column("Service", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Notes")

    for name, ok, note in results:
        status = "[green]✅ OK[/green]" if ok else "[red]❌ FAILED[/red]"
        table.add_row(name, status, note)

    console.print(table)

    all_ok = all(r[1] for r in results)
    if all_ok:
        console.print(
            "\n[bold green]All connections healthy — ready to build! 🚀[/bold green]")
    else:
        console.print(
            "\n[bold red]Some connections failed — check your .env file[/bold red]")
        console.print("  → Copy .env.example to .env and fill in your keys")

    return all_ok


if __name__ == "__main__":
    ok = run_checks()
    sys.exit(0 if ok else 1)
