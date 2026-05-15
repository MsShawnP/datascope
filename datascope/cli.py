"""Command-line interface for datascope.

Usage::

    datascope <input-file> [--output-dir DIR] [--sheet NAME_OR_INDEX] [--format FMT] [--version]

The CLI orchestrates the full analysis pipeline: load, analyse, classify,
compose, and render diagnostic output.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

from datascope import __version__

# Supported file extensions (lower-cased, with leading dot).
_SUPPORTED_EXTENSIONS = {".xlsx", ".csv"}


def _build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        prog="datascope",
        description=(
            "Analyse a tabular dataset (.xlsx or .csv) for data-quality issues\n"
            "and generate a professional PDF diagnostic report."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        help="Path to the .xlsx or .csv file to analyse.",
    )
    parser.add_argument(
        "--output-dir",
        default="./reports",
        help="Directory for the generated report (default: ./reports).",
    )
    parser.add_argument(
        "--sheet",
        default=None,
        help=(
            "Sheet name or 0-based index (Excel only). "
            "Default: first sheet (index 0)."
        ),
    )
    parser.add_argument(
        "--format",
        choices=["pdf", "json", "html", "both"],
        default="pdf",
        dest="output_format",
        help="Output format: pdf, json, html, or both (pdf+json). Default: pdf.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show full tracebacks when an analyzer fails.",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress stdout summary. Exit code 0 = no critical findings, 1 = critical findings present.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help=(
            "Maximum rows to process. Abort if exceeded. "
            "Default: warn at 500K cells, abort at 5M cells."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"datascope {__version__}",
    )

    return parser


def _parse_sheet(raw: str | None) -> str | int:
    """Convert the --sheet argument to an int (if numeric) or leave as str."""
    if raw is None:
        return 0
    try:
        return int(raw)
    except ValueError:
        return raw


def _format_summary(findings: list, source_metadata: dict, output_path: Path) -> str:
    """Build the human-readable stdout summary."""
    from datascope.models import Severity

    filename = source_metadata.get("filename", "unknown")
    rows = source_metadata.get("row_count", "?")
    cols = source_metadata.get("column_count", "?")

    lines: list[str] = []
    lines.append(f"datascope: Analyzing {filename}...")
    lines.append(f"  {rows} rows x {cols} columns")
    lines.append("")

    # Count by severity.
    counts: dict[Severity, int] = {s: 0 for s in Severity}
    for f in findings:
        if f.severity is not None:
            counts[f.severity] += 1

    total = sum(counts.values())
    lines.append(f"Found {total} finding{'s' if total != 1 else ''}:")

    # Severity labels, ordered CRITICAL first.
    severity_order = [Severity.CRITICAL, Severity.WARNING, Severity.INFO]
    label_map = {
        Severity.CRITICAL: "Critical",
        Severity.WARNING: "Warning",
        Severity.INFO: "Info",
    }

    max_count_width = max((len(str(counts[s])) for s in severity_order), default=1)

    for sev in severity_order:
        c = counts[sev]
        if c > 0:
            label = label_map[sev]
            bar = "#" * min(c * 4, 40)
            lines.append(f"  {c:>{max_count_width}} {label:<8} {bar}")

    if total == 0:
        lines.append("  No issues detected.")

    # Top critical findings (up to 5).
    critical = [f for f in findings if f.severity is Severity.CRITICAL]
    if critical:
        lines.append("")
        lines.append("Top critical findings:")
        for finding in critical[:5]:
            short = finding.reality or finding.assumption or "(no description)"
            lines.append(f"  * {finding.field_name}: {short}")

    lines.append("")
    lines.append(f"Report saved: {output_path}")

    return "\n".join(lines)


def _write_json(findings: list, source_metadata: dict, output_path: Path) -> None:
    """Write findings as structured JSON."""

    counts: dict[str, int] = {"critical": 0, "warning": 0, "info": 0, "total": 0}
    for f in findings:
        if f.severity is not None:
            counts[f.severity.name.lower()] += 1
            counts["total"] += 1

    payload = {
        "source": dict(source_metadata),
        "summary": counts,
        "findings": [
            {
                "field_name": f.field_name,
                "finding_type": f.finding_type.value,
                "severity": f.severity.name.lower() if f.severity else None,
                "assumption": f.assumption,
                "reality": f.reality,
                "impact": f.impact,
                "fix_recommendation": f.fix_recommendation,
                "prevention_rule": f.prevention_rule,
                "evidence": f.evidence,
            }
            for f in findings
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    """Entry point for the datascope CLI.

    Parameters
    ----------
    argv:
        Command-line arguments.  Defaults to ``sys.argv[1:]`` when *None*.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # --- validate input file --------------------------------------------
    if args.input_file is None:
        parser.print_help()
        sys.exit(1)

    input_path = Path(args.input_file)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    ext = input_path.suffix.lower()
    if ext not in _SUPPORTED_EXTENSIONS:
        print(
            f"Error: Unsupported file extension '{ext}'. "
            f"Supported: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- load -----------------------------------------------------------
    from datascope.loaders import load

    sheet = _parse_sheet(args.sheet)
    result = load(input_path, sheet=sheet)

    # --- size guard -----------------------------------------------------
    rows, cols = result.dataframe.shape
    cells = rows * cols
    max_rows = args.max_rows
    if max_rows is not None and rows > max_rows:
        print(
            f"Error: {rows:,} rows exceeds --max-rows limit of {max_rows:,}.",
            file=sys.stderr,
        )
        sys.exit(1)
    if max_rows is None:
        _WARN_CELLS = 500_000
        _ABORT_CELLS = 5_000_000
        if cells > _ABORT_CELLS:
            print(
                f"Error: {rows:,} rows x {cols:,} columns = {cells:,} cells "
                f"exceeds the {_ABORT_CELLS:,}-cell safety limit.\n"
                f"Use --max-rows to override.",
                file=sys.stderr,
            )
            sys.exit(1)
        if cells > _WARN_CELLS:
            print(
                f"Warning: {cells:,} cells is large — analysis may be slow.",
                file=sys.stderr,
            )

    # --- analyse --------------------------------------------------------
    from datascope.analyzers import (
        analyze_cardinality,
        analyze_leading_zeros,
        analyze_missing_values,
        analyze_mixed_dates,
        analyze_sentinels,
        analyze_type_consistency,
    )

    analyzers = [
        analyze_type_consistency,
        analyze_sentinels,
        analyze_leading_zeros,
        analyze_mixed_dates,
        analyze_cardinality,
        analyze_missing_values,
    ]

    all_findings: list = []
    for analyzer in analyzers:
        try:
            all_findings.extend(analyzer(result))
        except Exception as exc:
            if args.verbose:
                traceback.print_exc(file=sys.stderr)
            else:
                print(f"Warning: {analyzer.__name__} failed: {exc}", file=sys.stderr)

    # --- process --------------------------------------------------------
    from datascope.findings import process_findings

    processed = process_findings(all_findings)

    # --- report ---------------------------------------------------------
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fmt = args.output_format
    output_path = None

    if fmt in ("pdf", "both"):
        from datascope.reports import write_pdf

        output_name = f"{input_path.stem}_diagnostic.pdf"
        output_path = output_dir / output_name
        write_pdf(processed, result.source_metadata, output_path)

    if fmt in ("json", "both"):
        json_path = output_dir / f"{input_path.stem}_diagnostic.json"
        _write_json(processed, result.source_metadata, json_path)
        if output_path is None:
            output_path = json_path

    if fmt == "html":
        from datascope.reports import write_html

        html_path = output_dir / f"{input_path.stem}_diagnostic.html"
        write_html(processed, result.source_metadata, html_path)
        if output_path is None:
            output_path = html_path

    # --- stdout summary -------------------------------------------------
    if args.quiet:
        from datascope.models import Severity

        has_critical = any(f.severity is Severity.CRITICAL for f in processed)
        sys.exit(1 if has_critical else 0)

    print(_format_summary(processed, result.source_metadata, output_path))
