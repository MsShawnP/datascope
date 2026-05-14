"""Command-line interface for datascope.

Usage::

    datascope <input-file> [--output-dir DIR] [--sheet NAME_OR_INDEX] [--version]

The CLI orchestrates the full analysis pipeline: load, analyse, classify,
compose, and render a PDF diagnostic report.
"""

from __future__ import annotations

import argparse
import sys
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
    from datascope.loaders import load_excel, load_csv

    sheet = _parse_sheet(args.sheet)

    if ext == ".xlsx":
        result = load_excel(input_path, sheet=sheet)
    else:
        result = load_csv(input_path)

    # --- analyse --------------------------------------------------------
    from datascope.analyzers import (
        analyze_cardinality,
        analyze_leading_zeros,
        analyze_mixed_dates,
        analyze_sentinels,
        analyze_type_consistency,
    )

    all_findings: list = []
    all_findings.extend(analyze_type_consistency(result))
    all_findings.extend(analyze_sentinels(result))
    all_findings.extend(analyze_leading_zeros(result))
    all_findings.extend(analyze_mixed_dates(result))
    all_findings.extend(analyze_cardinality(result))

    # --- process --------------------------------------------------------
    from datascope.findings import process_findings

    processed = process_findings(all_findings)

    # --- report ---------------------------------------------------------
    from datascope.reports import write_pdf

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_name = f"{input_path.stem}_diagnostic.pdf"
    output_path = output_dir / output_name

    write_pdf(processed, result.source_metadata, output_path)

    # --- stdout summary -------------------------------------------------
    print(_format_summary(processed, result.source_metadata, output_path))
