"""
General-purpose deep research CLI (argparse entrypoint).

Use ``python run_deep_research.py`` from the repo root or ``deep-research`` after install.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from deep_research.main_process import DEFAULT_RECURSION_LIMIT, execute_main_process


def _slug_prefix(text: str, max_len: int = 40) -> str:
    """Derive a filesystem-safe default report prefix from query start."""
    s = re.sub(r"[^\w\s-]", "", text[:200], flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "_", s.strip()).strip("_")
    return (s[:max_len] or "research").lower()


def _load_query(args: argparse.Namespace) -> str:
    if args.query_file:
        p = Path(args.query_file).expanduser().resolve()
        if not p.is_file():
            print(f"[ERROR] Query file not found: {p}", file=sys.stderr)
            sys.exit(2)
        return p.read_text(encoding="utf-8").strip()
    if args.query:
        return args.query.strip()
    print("[ERROR] Provide --query or --query-file.", file=sys.stderr)
    sys.exit(2)


def _load_optional_file(path: str | None) -> str | None:
    if not path:
        return None
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        print(f"[ERROR] File not found: {p}", file=sys.stderr)
        sys.exit(2)
    return p.read_text(encoding="utf-8")


def _parse_preface(path: str | None) -> list[str] | None:
    if not path:
        return None
    text = _load_optional_file(path)
    if not text:
        return None
    return [line.rstrip("\n") for line in text.splitlines()]


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run deep research from a query or query file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--query",
        "-q",
        type=str,
        help="Research question or instructions (inline).",
    )
    g.add_argument(
        "--query-file",
        "-f",
        type=str,
        metavar="PATH",
        help="Path to a text/markdown file containing the research query.",
    )
    p.add_argument(
        "--output-path",
        "-o",
        type=str,
        default="reports/deep_research",
        help="Directory for reports, logs, and derived files.",
    )
    p.add_argument(
        "--report-prefix",
        type=str,
        default=None,
        help="Filename prefix for generated reports (default: slug from query).",
    )
    p.add_argument(
        "--task-name",
        type=str,
        default="deep_research",
        help="Task name for logging.",
    )
    p.add_argument(
        "--report-title",
        type=str,
        default="Research Report",
        help="Title in the main report header.",
    )
    p.add_argument(
        "--thread-id",
        type=str,
        default=None,
        help="Graph thread id (default: same as --task-name).",
    )
    p.add_argument(
        "--recursion-limit",
        type=int,
        default=DEFAULT_RECURSION_LIMIT,
        help="LangGraph recursion limit.",
    )
    p.add_argument(
        "--initial-report-file",
        type=str,
        default=None,
        metavar="PATH",
        help="Optional path to an initial report to enrich.",
    )
    p.add_argument(
        "--preface-file",
        type=str,
        default=None,
        metavar="PATH",
        help="Optional file; each line becomes a preface line in the main report.",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    query = _load_query(args)
    if not query:
        print("[ERROR] Query is empty.", file=sys.stderr)
        sys.exit(2)

    report_prefix = args.report_prefix or _slug_prefix(query)
    thread_id = args.thread_id or args.task_name
    initial_report = _load_optional_file(args.initial_report_file)
    preface_lines = _parse_preface(args.preface_file)

    report_path, summary_path = execute_main_process(
        query,
        output_path=args.output_path,
        report_prefix=report_prefix,
        task_name=args.task_name,
        report_title=args.report_title,
        preface_lines=preface_lines,
        thread_id=thread_id,
        recursion_limit=args.recursion_limit,
        initial_report=initial_report,
    )

    clean_report_path = report_path.parent / f"{report_path.stem}_cleaned.md"

    print(f"{report_path} - {clean_report_path}")
    if summary_path:
        print(f"[summary] {summary_path}")


if __name__ == "__main__":
    main()
