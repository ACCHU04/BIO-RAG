"""
Quick demo script — ingest sample data and run a test query.
Run: python scripts/demo.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from app.agent.graph import run_agent
from app.rag.retriever import ingest_documents

console = Console()

SAMPLE_QUERIES = [
    "What genes are implicated in both Alzheimer's disease and Type 2 Diabetes?",
    "What is the mechanism of BRCA1 in DNA repair and how does it relate to cancer?",
    "Which drugs target the EGFR pathway in non-small cell lung cancer?",
]

def main():
    console.print(Panel.fit(
        "[bold blue]Biomedical Agentic RAG — Demo[/bold blue]\n"
        "Domain: Drug-Gene-Disease Relationship Intelligence",
        border_style="blue"
    ))

    # Ingest any docs in data/documents
    console.print("\n[yellow]Step 1: Ingesting documents...[/yellow]")
    count = ingest_documents("./data/documents")
    console.print(f"[green][OK] Ingested {count} chunks[/green]")

    # Run a sample query
    query = SAMPLE_QUERIES[0]
    console.print(f"\n[yellow]Step 2: Running agent query...[/yellow]")
    console.print(f"[dim]Query: {query}[/dim]\n")

    result = run_agent(query)

    console.print(Panel(result["answer"], title="[bold green]Agent Answer[/bold green]", border_style="green"))

    table = Table(title="Agent Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Self-corrections", str(result["self_corrections"]))
    table.add_row("PubMed articles used", str(result["pubmed_count"]))
    table.add_row("Local docs used", str(result["local_docs_count"]))
    table.add_row("Reasoning steps", str(len(result["reasoning_steps"])))
    console.print(table)

    console.print("\n[dim]Reasoning trace:[/dim]")
    for i, step in enumerate(result["reasoning_steps"], 1):
        console.print(f"  [dim]{i}. {step}[/dim]")

if __name__ == "__main__":
    main()
