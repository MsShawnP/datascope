"""HTML report generator for datascope findings.

Renders findings into a self-contained HTML file with inline CSS.
Mirrors the PDF report structure: title, executive summary, findings
by severity, and field inventory.
"""

from __future__ import annotations

import datetime
import html
from collections import defaultdict
from pathlib import Path
from typing import Any

from datascope.models import Finding, FindingType, Severity

_SEVERITY_ORDER = [Severity.CRITICAL, Severity.WARNING, Severity.INFO]

_SEVERITY_LABELS = {
    Severity.CRITICAL: "Critical",
    Severity.WARNING: "Warning",
    Severity.INFO: "Info",
}

_SEVERITY_COLORS = {
    Severity.CRITICAL: ("#C0392B", "#FADBD8"),
    Severity.WARNING: ("#E67E22", "#FDEBD0"),
    Severity.INFO: ("#2E86AB", "#D6EAF8"),
}

_FINDING_TYPE_LABELS: dict[FindingType, str] = {
    FindingType.TYPE_INCONSISTENCY: "Type Inconsistency",
    FindingType.SENTINEL_VALUE: "Sentinel Value",
    FindingType.LEADING_ZEROS: "Leading Zeros",
    FindingType.MIXED_DATES: "Mixed Date Formats",
    FindingType.NEAR_CONSTANT: "Near-Constant Column",
    FindingType.DUPLICATE_IDS: "Suspected Duplicate IDs",
    FindingType.MISSING_VALUE_PATTERN: "Missing Values",
}


def _e(text: str | None) -> str:
    """HTML-escape a string."""
    if text is None:
        return ""
    return html.escape(str(text))


def _health_assessment(findings: list[Finding]) -> str:
    counts: dict[Severity, int] = {s: 0 for s in Severity}
    for f in findings:
        if f.severity is not None:
            counts[f.severity] += 1

    crit = counts[Severity.CRITICAL]
    warn = counts[Severity.WARNING]
    info = counts[Severity.INFO]

    if crit > 0:
        return (
            f"This dataset has {crit} critical finding{'s' if crit != 1 else ''} "
            f"that will cause silent data loss or incorrect calculations if not addressed. "
            f"These should be fixed before using this data for any downstream purpose."
        )
    if warn > 0:
        return (
            f"No critical issues were found, but {warn} warning{'s' if warn != 1 else ''} "
            f"indicate{'s' if warn == 1 else ''} potential problems that could cause "
            f"misinterpretation or key mismatches."
        )
    if info > 0:
        return (
            f"{info} informational observation{'s were' if info != 1 else ' was'} "
            f"found. The dataset is in good shape overall."
        )
    return "No issues detected. The dataset looks clean."


def _render_finding_card(finding: Finding) -> str:
    sev = finding.severity or Severity.INFO
    accent, tint = _SEVERITY_COLORS[sev]
    label = _SEVERITY_LABELS[sev]
    type_label = _FINDING_TYPE_LABELS.get(finding.finding_type, finding.finding_type.value)

    sections = []
    if finding.assumption:
        sections.append(f'<p><strong>Assumption:</strong> {_e(finding.assumption)}</p>')
    if finding.reality:
        sections.append(f'<p><strong>Reality:</strong> {_e(finding.reality)}</p>')
    if finding.impact:
        sections.append(f'<p><strong>Impact:</strong> {_e(finding.impact)}</p>')
    if finding.fix_recommendation:
        sections.append(f'<p><strong>Recommended Fix:</strong> {_e(finding.fix_recommendation)}</p>')
    if finding.prevention_rule:
        sections.append(f'<p><strong>Prevention Rule:</strong> {_e(finding.prevention_rule)}</p>')

    body = "\n".join(sections)

    return f"""
    <div class="finding-card" style="border-left: 4px solid {accent}; background: {tint};">
      <div class="finding-header">
        <span class="badge" style="background: {accent};">{label}</span>
        <span class="field-name">{_e(finding.field_name)}</span>
        <span class="finding-type">{_e(type_label)}</span>
      </div>
      <div class="finding-body">
        {body}
      </div>
    </div>
    """


def write_html(
    findings: list[Finding],
    source_metadata: dict[str, Any],
    output_path: Path,
) -> None:
    """Write findings as a self-contained HTML report."""
    filename = source_metadata.get("filename", "unknown")
    rows = source_metadata.get("row_count", "?")
    cols = source_metadata.get("column_count", "?")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    counts: dict[Severity, int] = {s: 0 for s in Severity}
    for f in findings:
        if f.severity is not None:
            counts[f.severity] += 1
    total = sum(counts.values())

    grouped: dict[Severity, list[Finding]] = defaultdict(list)
    for f in findings:
        grouped[f.severity or Severity.INFO].append(f)

    health = _health_assessment(findings)

    summary_cards = ""
    for sev in _SEVERITY_ORDER:
        accent, _ = _SEVERITY_COLORS[sev]
        label = _SEVERITY_LABELS[sev]
        c = counts[sev]
        summary_cards += f"""
        <div class="summary-card" style="border-top: 3px solid {accent};">
          <div class="summary-number">{c}</div>
          <div class="summary-label">{label}</div>
        </div>
        """

    finding_sections = ""
    for sev in _SEVERITY_ORDER:
        if sev not in grouped:
            continue
        label = _SEVERITY_LABELS[sev]
        cards = "\n".join(_render_finding_card(f) for f in grouped[sev])
        finding_sections += f"""
        <h2>{label} Findings</h2>
        {cards}
        """

    field_rows = ""
    for f in findings:
        sev = f.severity or Severity.INFO
        accent, _ = _SEVERITY_COLORS[sev]
        label = _SEVERITY_LABELS[sev]
        type_label = _FINDING_TYPE_LABELS.get(f.finding_type, f.finding_type.value)
        field_rows += f"""
        <tr>
          <td>{_e(f.field_name)}</td>
          <td>{_e(type_label)}</td>
          <td><span class="badge-sm" style="background: {accent};">{label}</span></td>
        </tr>
        """

    from datascope import __version__

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Data quality diagnostic report for {_e(filename)} — generated by datascope v{__version__}">
<meta name="generator" content="datascope v{__version__}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='40' fill='%231F3864'/><text x='50' y='62' font-size='40' text-anchor='middle' fill='white' font-family='sans-serif' font-weight='bold'>d</text></svg>">
<title>datascope diagnostic — {_e(filename)}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         color: #333; background: #f5f6fa; line-height: 1.6; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
  .title-section {{ text-align: center; padding: 40px 0 20px; }}
  .title-section h1 {{ color: #1F3864; font-size: 28px; margin-bottom: 4px; }}
  .title-section .subtitle {{ color: #888; font-size: 14px; }}
  .summary-row {{ display: flex; gap: 16px; margin: 20px 0; justify-content: center; }}
  .summary-card {{ background: white; border-radius: 8px; padding: 20px 32px;
                   text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  .summary-number {{ font-size: 32px; font-weight: bold; color: #1F3864; }}
  .summary-label {{ font-size: 13px; color: #666; }}
  .health {{ background: white; border-radius: 8px; padding: 16px 20px;
             margin: 16px 0 24px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  .health p {{ font-size: 14px; }}
  h2 {{ color: #1F3864; font-size: 18px; margin: 28px 0 12px; }}
  .finding-card {{ background: white; border-radius: 8px; padding: 16px 20px;
                   margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  .finding-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
  .badge {{ color: white; font-size: 11px; font-weight: 600; padding: 2px 10px;
            border-radius: 4px; text-transform: uppercase; }}
  .badge-sm {{ color: white; font-size: 10px; font-weight: 600; padding: 1px 8px;
               border-radius: 3px; }}
  .field-name {{ font-weight: 600; font-size: 15px; color: #1F3864; }}
  .finding-type {{ font-size: 12px; color: #888; }}
  .finding-body p {{ font-size: 13px; margin-bottom: 6px; }}
  .finding-body strong {{ color: #1F3864; }}
  table {{ width: 100%; border-collapse: collapse; background: white;
           border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  th {{ background: #1F3864; color: white; padding: 10px 14px; text-align: left; font-size: 13px; }}
  td {{ padding: 8px 14px; font-size: 13px; border-bottom: 1px solid #eee; }}
  tr:nth-child(even) {{ background: #f9fafb; }}
  .footer {{ text-align: center; padding: 24px 0; color: #aaa; font-size: 12px; }}
</style>
</head>
<body>
<div class="container">
  <div class="title-section">
    <h1>datascope diagnostic</h1>
    <div class="subtitle">{_e(filename)} &middot; {rows} rows &times; {cols} columns &middot; {now}</div>
  </div>

  <div class="summary-row">
    {summary_cards}
  </div>

  <div class="health">
    <p><strong>Health Assessment:</strong> {_e(health)}</p>
  </div>

  {finding_sections}

  <h2>Field Inventory</h2>
  <table>
    <thead><tr><th>Field</th><th>Issue Type</th><th>Severity</th></tr></thead>
    <tbody>{field_rows}</tbody>
  </table>

  <div class="footer">
    Generated by datascope v{__version__} &middot; {now} &middot; {total} finding{'s' if total != 1 else ''}
    <br>pip install datascope-dq
  </div>
</div>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(page, encoding="utf-8")
