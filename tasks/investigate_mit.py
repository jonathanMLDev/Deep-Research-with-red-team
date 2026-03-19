"""
Main entry point for MIT-license attribution research task.

This script provides a command-line interface to run deep research queries.
"""

import os
import sys
import traceback
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from deep_research.main_process import execute_main_process

# Initialize console for rich output
console = Console()

OUTPUT_PATH = "report_for_MIT"


def create_research_query() -> str:
    """
    Return the research query, preferring ``prompt.txt`` in the repo root.

    If ``prompt.txt`` is missing, unreadable, or empty, returns the built-in
    default MIT-attribution research brief.

    Returns:
        The research query string.
    """
    default_query = """I need to write an up-to-date report titled "Notable Companies That Avoid Using MIT-Licensed Code Due to Binary Attribution Requirements".

Please research and report on the existence of cases among large, market-influential companies that have an explicit, documented practice of avoiding MIT-licensed code specifically because of the MIT license's requirement to preserve copyright and license notices in distributed binaries or user-facing products.

Requirements:
- Cross-reference multiple sources before asserting conclusions
- Clearly cite all references with full URLs
- Prioritize companies based on market impact and influence
- Focus on factual, verifiable information
- Include both positive findings (companies that do avoid MIT) and negative findings (no such companies found) if that's what the evidence shows
- Provide a comprehensive list of references at the end of the report

Note: Boost License (BSL-1.0) is convenient because it does not have binary attribution requirements, but this research should focus specifically on MIT license avoidance due to attribution requirements."""

    prompt_path = Path(__file__).resolve().parent.parent / "prompt.txt"
    if prompt_path.is_file():
        try:
            text = prompt_path.read_text(encoding="utf-8").strip()
            if text:
                return text
        except OSError:
            pass
    return default_query


def main():
    """Main entry point for the CLI."""
    console.print("\n[bold cyan]Starting Deep Research...[/bold cyan]")

    # Get query from command line or prompt user
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        console.print("[bold]ThinkDepth.ai Deep Research[/bold]")
        console.print(
            "[dim]Enter your research query (or press Ctrl+C to exit)[/dim]\n"
        )
        query = create_research_query()

        if not query:
            console.print("[red]No query provided. Exiting.[/red]")
            sys.exit(1)

    # Optional: Get thread_id from environment or use default
    thread_id = os.getenv("RESEARCH_THREAD_ID", "default")

    # Optional: Get recursion limit from environment or use default
    try:
        recursion_limit = int(os.getenv("RESEARCH_RECURSION_LIMIT", "50"))
    except ValueError:
        recursion_limit = 50

    # Run the research
    try:
        report_path, summary_path = execute_main_process(
            query,
            output_path=OUTPUT_PATH,
            report_prefix="research_report",
            task_name="investigate_mit",
            report_title="Research Report",
            thread_id=thread_id,
            recursion_limit=recursion_limit,
        )

        console.print(f"[green]Report saved to: {report_path}[/green]")
        if summary_path:
            console.print(f"[green]Summary saved to: {summary_path}[/green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Research interrupted by user.[/yellow]")
        sys.exit(1)
    except RuntimeError as e:
        # Handle API-related errors with better formatting
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            console.print(
                Panel(
                    error_msg + "\n\n"
                    "[yellow]To resolve this issue:[/yellow]\n"
                    "1. Check your OpenAI account usage: https://platform.openai.com/usage\n"
                    "2. Verify your billing information is set up\n"
                    "3. Consider upgrading your plan if you've hit usage limits\n"
                    "4. Wait for your quota to reset if you're on a free tier",
                    title="[bold red]API Quota Error[/bold red]",
                    border_style="red",
                )
            )
        elif "api key" in error_msg.lower() or "401" in error_msg:
            console.print(
                Panel(
                    error_msg + "\n\n"
                    "[yellow]To resolve this issue:[/yellow]\n"
                    "1. Verify your OPENAI_API_KEY in your .env file\n"
                    "2. Make sure the key is correct and not expired\n"
                    "3. Check that your .env file is in the project root directory",
                    title="[bold red]API Key Error[/bold red]",
                    border_style="red",
                )
            )
        else:
            console.print(
                Panel(
                    error_msg,
                    title="[bold red]Runtime Error[/bold red]",
                    border_style="red",
                )
            )
        sys.exit(1)
    except Exception as e:
        traceback.print_exc()
        console.print(
            Panel(
                f"[bold red]Unexpected error:[/bold red]\n{e!s}\n\n"
                "If this is an API error, check your API keys and quota limits.",
                title="[bold red]Fatal Error[/bold red]",
                border_style="red",
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
