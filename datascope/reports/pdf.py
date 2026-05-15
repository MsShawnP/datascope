"""PDF report generator for datascope findings.

Renders a list of :class:`~datascope.models.Finding` objects into a
professional, client-ready PDF using reportlab.  The report is structured
for non-technical readers: no jargon, no unexplained statistical metrics.

Sections:
1. Title page with finding count summary
2. Executive summary -- overall health assessment and critical highlights
3. Findings by severity -- grouped and color-coded cards
4. Field inventory -- summary table of all analyzed columns
"""

from __future__ import annotations

import datetime
from collections import defaultdict
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from datascope.models import Finding, FindingType, Severity

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

NAVY = colors.HexColor("#1F3864")
LIGHT_BLUE = colors.HexColor("#D9E1F2")
ALT_ROW = colors.HexColor("#EEF2F7")
WHITE = colors.white

# Severity colours -- professional tones.
CRITICAL_BG = colors.HexColor("#C0392B")
WARNING_BG = colors.HexColor("#E67E22")
INFO_BG = colors.HexColor("#2E86AB")

# Lighter tints for card backgrounds.
CRITICAL_TINT = colors.HexColor("#FADBD8")
WARNING_TINT = colors.HexColor("#FDEBD0")
INFO_TINT = colors.HexColor("#D6EAF8")

GRID_COLOR = colors.HexColor("#CCCCCC")

_SEVERITY_COLORS: dict[Severity, colors.HexColor] = {
    Severity.CRITICAL: CRITICAL_BG,
    Severity.WARNING: WARNING_BG,
    Severity.INFO: INFO_BG,
}

_SEVERITY_TINTS: dict[Severity, colors.HexColor] = {
    Severity.CRITICAL: CRITICAL_TINT,
    Severity.WARNING: WARNING_TINT,
    Severity.INFO: INFO_TINT,
}

_SEVERITY_LABELS: dict[Severity, str] = {
    Severity.CRITICAL: "Critical",
    Severity.WARNING: "Warning",
    Severity.INFO: "Info",
}

_FINDING_TYPE_LABELS: dict[FindingType, str] = {
    FindingType.TYPE_INCONSISTENCY: "Type Inconsistency",
    FindingType.SENTINEL_VALUE: "Sentinel Value",
    FindingType.LEADING_ZEROS: "Leading Zeros",
    FindingType.MIXED_DATES: "Mixed Date Formats",
    FindingType.NEAR_CONSTANT: "Near-Constant Column",
    FindingType.DUPLICATE_IDS: "Suspected Duplicate IDs",
}

# Page geometry.
PAGE_W, PAGE_H = letter
CONTENT_W = PAGE_W - 1.0 * inch  # 0.5in margin each side


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _build_styles() -> dict[str, ParagraphStyle]:
    """Create the paragraph styles used throughout the report."""
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "ds_title", parent=base["Title"],
            fontSize=24, textColor=NAVY, spaceAfter=6,
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "ds_subtitle", parent=base["Normal"],
            fontSize=12, textColor=colors.grey, spaceAfter=4,
            alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "ds_h1", parent=base["Heading1"],
            fontSize=16, textColor=NAVY, spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "ds_h2", parent=base["Heading2"],
            fontSize=13, textColor=NAVY, spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "ds_h3", parent=base["Heading3"],
            fontSize=11, textColor=NAVY, spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "ds_body", parent=base["Normal"],
            fontSize=9, spaceAfter=4, leading=13,
        ),
        "body_bold": ParagraphStyle(
            "ds_body_bold", parent=base["Normal"],
            fontSize=9, spaceAfter=4, leading=13,
            fontName="Helvetica-Bold",
        ),
        "caption": ParagraphStyle(
            "ds_caption", parent=base["Normal"],
            fontSize=8, textColor=colors.grey, spaceAfter=6,
        ),
        "badge": ParagraphStyle(
            "ds_badge", parent=base["Normal"],
            fontSize=9, textColor=WHITE, alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        ),
        "summary_number": ParagraphStyle(
            "ds_summary_number", parent=base["Normal"],
            fontSize=28, alignment=TA_CENTER,
            fontName="Helvetica-Bold", leading=34, spaceAfter=0,
        ),
        "summary_label": ParagraphStyle(
            "ds_summary_label", parent=base["Normal"],
            fontSize=10, alignment=TA_CENTER,
            fontName="Helvetica-Bold", spaceAfter=0,
        ),
        "card_label": ParagraphStyle(
            "ds_card_label", parent=base["Normal"],
            fontSize=8, textColor=colors.grey, spaceAfter=1,
            fontName="Helvetica-Bold",
        ),
        "card_text": ParagraphStyle(
            "ds_card_text", parent=base["Normal"],
            fontSize=9, spaceAfter=4, leading=12,
        ),
        "no_issues": ParagraphStyle(
            "ds_no_issues", parent=base["Normal"],
            fontSize=12, textColor=colors.HexColor("#27AE60"),
            alignment=TA_CENTER, spaceAfter=10,
        ),
    }


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _severity_counts(findings: list[Finding]) -> dict[Severity, int]:
    """Count findings per severity level."""
    counts: dict[Severity, int] = {s: 0 for s in Severity}
    for f in findings:
        if f.severity is not None:
            counts[f.severity] += 1
    return counts


def _build_title_page(
    story: list,
    styles: dict[str, ParagraphStyle],
    source_metadata: dict[str, Any],
    counts: dict[Severity, int],
) -> None:
    """Append the title page flowables to *story*."""
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("Data Quality Diagnostic Report", styles["title"]))
    story.append(Spacer(1, 0.1 * inch))

    filename = _safe(source_metadata.get("filename", "Unknown source"))
    story.append(Paragraph(f"Source: {filename}", styles["subtitle"]))

    date_str = datetime.date.today().strftime("%B %d, %Y")
    story.append(Paragraph(date_str, styles["subtitle"]))
    story.append(Spacer(1, 0.3 * inch))

    story.append(HRFlowable(width="60%", thickness=2, color=NAVY))
    story.append(Spacer(1, 0.3 * inch))

    # Summary counts as a small centered table.
    total = sum(counts.values())
    summary_data = [[
        Paragraph(str(counts[Severity.CRITICAL]), styles["summary_number"]),
        Paragraph(str(counts[Severity.WARNING]), styles["summary_number"]),
        Paragraph(str(counts[Severity.INFO]), styles["summary_number"]),
    ], [
        Paragraph("Critical", styles["summary_label"]),
        Paragraph("Warning", styles["summary_label"]),
        Paragraph("Info", styles["summary_label"]),
    ]]
    summary_tbl = Table(
        summary_data,
        colWidths=[1.8 * inch] * 3,
        rowHeights=[0.5 * inch, 0.25 * inch],
    )
    summary_tbl.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "BOTTOM"),
        ("VALIGN", (0, 1), (-1, 1), "TOP"),
        ("TEXTCOLOR", (0, 0), (0, 0), CRITICAL_BG),
        ("TEXTCOLOR", (1, 0), (1, 0), WARNING_BG),
        ("TEXTCOLOR", (2, 0), (2, 0), INFO_BG),
        ("TEXTCOLOR", (0, 1), (0, 1), CRITICAL_BG),
        ("TEXTCOLOR", (1, 1), (1, 1), WARNING_BG),
        ("TEXTCOLOR", (2, 1), (2, 1), INFO_BG),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
    ]))
    story.append(summary_tbl)

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        f"{total} finding{'s' if total != 1 else ''} across "
        f"{source_metadata.get('column_count', 'N/A')} columns and "
        f"{source_metadata.get('row_count', 'N/A')} rows",
        styles["subtitle"],
    ))
    story.append(PageBreak())


def _health_assessment(counts: dict[Severity, int]) -> str:
    """Return a plain-English health assessment based on severity counts."""
    total = sum(counts.values())
    crit = counts[Severity.CRITICAL]
    warn = counts[Severity.WARNING]

    if total == 0:
        return (
            "No data quality issues were detected. The dataset appears clean "
            "and ready for analysis."
        )
    info = counts[Severity.INFO]
    if crit == 0 and warn == 0:
        return (
            f"{info} informational observation{'s were' if info != 1 else ' was'} "
            f"found. The dataset is in good shape overall, with "
            f"{'a few' if info <= 3 else 'some'} minor items worth noting."
        )
    if crit == 0:
        return (
            f"No critical issues were found, but {warn} "
            f"warning{'s' if warn != 1 else ''} and {info} informational "
            f"observation{'s were' if info != 1 else ' was'} detected. "
            f"Address the warnings before using this data in production."
        )
    if crit <= 2:
        return (
            f"This dataset has {crit} critical issue{'s' if crit != 1 else ''} "
            f"that could cause silent data loss or incorrect calculations. "
            f"These should be resolved before the data is used for reporting "
            f"or analysis."
        )
    return (
        f"This dataset has {crit} critical issues that require immediate "
        f"attention. Data used in its current state is likely to produce "
        f"incorrect results. A thorough review and cleanup is recommended "
        f"before proceeding."
    )


def _build_executive_summary(
    story: list,
    styles: dict[str, ParagraphStyle],
    findings: list[Finding],
    counts: dict[Severity, int],
) -> None:
    """Append the executive summary section to *story*."""
    story.append(Paragraph("Executive Summary", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph(_health_assessment(counts), styles["body"]))
    story.append(Spacer(1, 0.15 * inch))

    # Highlight critical findings (up to 3).
    critical = [f for f in findings if f.severity is Severity.CRITICAL]
    if critical:
        story.append(Paragraph("Top Critical Findings", styles["h2"]))
        for finding in critical[:3]:
            label = _FINDING_TYPE_LABELS.get(finding.finding_type, "Issue")
            text = (
                f"<b>{_safe(finding.field_name)}</b> ({label}): "
                f"{_safe(finding.reality or '')}"
            )
            story.append(Paragraph(text, styles["body"]))
        if len(critical) > 3:
            story.append(Paragraph(
                f"... and {len(critical) - 3} more critical "
                f"finding{'s' if len(critical) - 3 != 1 else ''} below.",
                styles["caption"],
            ))
        story.append(Spacer(1, 0.1 * inch))

    story.append(PageBreak())


def _safe(text: str) -> str:
    """Escape XML-sensitive characters for Paragraph markup."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _build_finding_card(
    finding: Finding,
    styles: dict[str, ParagraphStyle],
) -> list:
    """Build a list of flowables representing one finding card."""
    sev = finding.severity or Severity.INFO
    tint = _SEVERITY_TINTS.get(sev, INFO_TINT)
    badge_color = _SEVERITY_COLORS.get(sev, INFO_BG)
    badge_label = _SEVERITY_LABELS.get(sev, "Info")
    type_label = _FINDING_TYPE_LABELS.get(finding.finding_type, "Issue")

    # Card header row: badge | field name | finding type
    badge_style = ParagraphStyle(
        "badge_inline", parent=styles["badge"],
        backColor=badge_color,
        borderPadding=(2, 6, 2, 6),
    )
    badge_para = Paragraph(badge_label, badge_style)

    header_data = [[
        badge_para,
        Paragraph(
            f"<b>{_safe(finding.field_name)}</b>",
            styles["body_bold"],
        ),
        Paragraph(type_label, styles["caption"]),
    ]]
    header_tbl = Table(
        header_data,
        colWidths=[0.9 * inch, CONTENT_W - 2.5 * inch, 1.6 * inch],
    )
    header_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), tint),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    # Card body: five narrative fields in labeled rows.
    fields = [
        ("Assumption", finding.assumption),
        ("Reality", finding.reality),
        ("Impact", finding.impact),
        ("Recommended Fix", finding.fix_recommendation),
        ("Prevention Rule", finding.prevention_rule),
    ]
    body_rows = []
    for label, text in fields:
        body_rows.append([
            Paragraph(label, styles["card_label"]),
            Paragraph(_safe(text or "(not available)"), styles["card_text"]),
        ])

    body_tbl = Table(
        body_rows,
        colWidths=[1.3 * inch, CONTENT_W - 1.3 * inch],
    )
    body_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, GRID_COLOR),
    ]))

    # Wrap card in a border.
    card_data = [
        [header_tbl],
        [body_tbl],
    ]
    card_tbl = Table(card_data, colWidths=[CONTENT_W])
    card_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, GRID_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    return [KeepTogether([card_tbl, Spacer(1, 0.1 * inch)])]


def _build_findings_section(
    story: list,
    styles: dict[str, ParagraphStyle],
    findings: list[Finding],
) -> None:
    """Append the findings-by-severity section to *story*."""
    story.append(Paragraph("Detailed Findings", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY))
    story.append(Spacer(1, 0.1 * inch))

    if not findings:
        story.append(Paragraph(
            "No data quality issues were found.",
            styles["no_issues"],
        ))
        return

    # Group by severity, then by field_name within each tier.
    for severity in (Severity.CRITICAL, Severity.WARNING, Severity.INFO):
        tier_findings = [f for f in findings if f.severity is severity]
        if not tier_findings:
            continue

        label = _SEVERITY_LABELS[severity]
        color = _SEVERITY_COLORS[severity]
        story.append(Paragraph(
            f"{label} ({len(tier_findings)})",
            ParagraphStyle(
                f"sev_header_{severity.name}",
                parent=styles["h2"],
                textColor=color,
            ),
        ))
        story.append(Spacer(1, 0.05 * inch))

        # Sub-group by field_name so related issues appear together.
        by_field: dict[str, list[Finding]] = defaultdict(list)
        for f in tier_findings:
            by_field[f.field_name].append(f)

        for field_name in sorted(by_field):
            for finding in by_field[field_name]:
                story.extend(_build_finding_card(finding, styles))

    story.append(PageBreak())


def _build_field_inventory(
    story: list,
    styles: dict[str, ParagraphStyle],
    findings: list[Finding],
    source_metadata: dict[str, Any],
) -> None:
    """Append the field inventory table to *story*."""
    story.append(Paragraph("Field Inventory", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "Summary of all fields with detected issues.",
        styles["caption"],
    ))

    if not findings:
        story.append(Paragraph(
            "No fields with issues to display.",
            styles["body"],
        ))
        return

    # Collect per-field info.
    field_data: dict[str, dict] = defaultdict(lambda: {
        "types": set(),
        "severities": set(),
        "count": 0,
    })
    for f in findings:
        entry = field_data[f.field_name]
        entry["types"].add(_FINDING_TYPE_LABELS.get(f.finding_type, "Other"))
        if f.severity is not None:
            entry["severities"].add(f.severity)
        entry["count"] += 1

    # Build table rows.
    header = ["Field Name", "Issue Types", "Highest Severity", "Finding Count"]
    rows = [header]
    for field_name in sorted(field_data):
        entry = field_data[field_name]
        types_str = ", ".join(sorted(entry["types"]))
        if entry["severities"]:
            max_sev = max(entry["severities"])
            sev_str = _SEVERITY_LABELS.get(max_sev, "Unknown")
        else:
            sev_str = "Unknown"
        rows.append([field_name, types_str, sev_str, str(entry["count"])])

    col_widths = [2.0 * inch, 2.5 * inch, 1.5 * inch, 1.0 * inch]
    # Scale to fit content width.
    total_w = sum(col_widths)
    if total_w > CONTENT_W:
        scale = CONTENT_W / total_w
        col_widths = [w * scale for w in col_widths]

    tbl = Table(rows, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),
        ("ALIGN", (3, 1), (3, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ALT_ROW]),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]

    # Colour-code the severity column per row.
    for row_idx in range(1, len(rows)):
        sev_text = rows[row_idx][2]
        for sev, label in _SEVERITY_LABELS.items():
            if sev_text == label:
                style_cmds.append(
                    ("TEXTCOLOR", (2, row_idx), (2, row_idx), _SEVERITY_COLORS[sev])
                )
                style_cmds.append(
                    ("FONTNAME", (2, row_idx), (2, row_idx), "Helvetica-Bold")
                )
                break

    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def write_pdf(
    findings: list[Finding],
    source_metadata: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """Render findings into a professional PDF report.

    Parameters
    ----------
    findings:
        Sorted list of complete :class:`~datascope.models.Finding` objects
        (already processed by :func:`~datascope.findings.pipeline.process_findings`).
    source_metadata:
        Dict with keys like ``"filename"``, ``"row_count"``,
        ``"column_count"``.
    output_path:
        Filesystem path for the generated PDF.  Parent directories are
        created automatically if they do not exist.

    Returns
    -------
    Path
        The resolved path to the created PDF file.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    filename = source_metadata.get("filename", "Unknown source")

    def _on_later_pages(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(
            0.5 * inch, letter[1] - 0.4 * inch,
            f"datascope diagnostic — {filename}",
        )
        canvas.drawRightString(
            letter[0] - 0.5 * inch, 0.35 * inch,
            f"Page {canvas.getPageNumber()}",
        )
        canvas.restoreState()

    styles = _build_styles()
    counts = _severity_counts(findings)
    story: list = []

    _build_title_page(story, styles, source_metadata, counts)
    _build_executive_summary(story, styles, findings, counts)
    _build_findings_section(story, styles, findings)
    _build_field_inventory(story, styles, findings, source_metadata)

    doc.build(story, onLaterPages=_on_later_pages)
    return output
