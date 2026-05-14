# datascope

Data created upstream — by manufacturing teams entering UPCs, inventory staff assigning product codes, offshore developers choosing column types — silently breaks systems downstream. A product code with letters where EDI expects numbers. Fifteen "N/A" strings buried in 500 numeric rows that pandas silently drops, skewing every calculation by 3%.

datascope finds these problems, explains what's wrong in plain English, and tells you what to fix. It reads each cell's actual type (not what pandas infers), detects hidden quality issues, classifies their severity by downstream impact, and generates a professional diagnostic report.

---

## What It Finds

| Detection | Example | Severity |
|---|---|---|
| **Mixed types** | 485 numbers + 15 strings in a "numeric" column | Critical |
| **Sentinel values** | "N/A", "TBD", "pending" hiding in numeric data | Critical |
| **Leading-zero inconsistency** | "00123" alongside "456" — keys that won't match | Warning |
| **Mixed date formats** | "01/15/2026" and "2026-01-15" in the same column | Warning |
| **Suspected duplicate IDs** | 98% unique in an ID column — the other 2% will fan out joins | Warning |
| **Near-constant columns** | 1 distinct value across 10,000 rows | Info |

Each finding is expressed as **assumption vs. reality**: what the data *appears* to be vs. what it *actually contains*. Every finding includes a downstream impact explanation, a fix recommendation, and a prevention rule.

---

## Installation

```bash
git clone https://github.com/MsShawnP/field-story-scorer.git
cd field-story-scorer
pip install -e .
```

---

## Usage

```bash
# Analyze an Excel file
datascope data.xlsx

# Analyze a CSV
datascope sales_export.csv

# Specify a sheet and output directory
datascope data.xlsx --sheet Revenue --output-dir ./client_reports
```

The tool produces a PDF diagnostic report and prints a summary to stdout:

```
datascope: Analyzing sample_mixed_types.xlsx...
  200 rows x 6 columns

Found 4 findings:
  2 Critical  ########
  1 Warning   ####
  1 Info      ####

Top critical findings:
  * revenue_mixed: 15 non-numeric values hiding in an otherwise numeric column
  * status: Sentinel values 'N/A' and 'TBD' in numeric data

Report saved: reports/sample_mixed_types_diagnostic.pdf
```

---

## The Report

The PDF report is structured for non-technical readers — no jargon, no composite scores, no unexplained metrics.

**Executive Summary** — overall health assessment, finding counts by severity, top critical issues highlighted.

**Findings by Severity** — each finding presented as a card:
- **Assumption**: what the data appears to be
- **Reality**: what it actually contains
- **Impact**: what breaks downstream
- **Recommended Fix**: what to do now
- **Prevention Rule**: what right looks like going forward

**Field Inventory** — summary table of all columns with their detected issue types and severity.

Findings are color-coded (red/amber/blue) and grouped by severity so readers know what to fix first.

---

## How It Works

Most tools let pandas (or the SQL driver, or Excel) decide column types. A column with 485 numbers and 15 strings becomes `float64` — the strings become `NaN`, the type problem disappears, and every downstream calculation is quietly wrong.

datascope reads each cell's actual Python type via openpyxl (for Excel) or raw-string inference (for CSV). This cell-level type detection is always on — there's no flag to enable it because skipping it defeats the purpose.

The analysis pipeline:

1. **Load** — read with cell-level type preservation (no silent coercion)
2. **Detect** — five analyzers scan for type inconsistencies, sentinels, format issues, and cardinality anomalies
3. **Classify** — severity assigned by downstream impact (critical = silent data loss, warning = likely misinterpretation, info = worth noting)
4. **Compose** — plain-English narrative generated for each finding
5. **Report** — professional PDF rendered with reportlab

---

## Severity Model

| Level | Meaning | Examples |
|---|---|---|
| **Critical** | Silent data loss or incorrect calculations will occur | Mixed types in numeric columns; sentinel values pandas drops without warning |
| **Warning** | Key mismatches or misinterpretation likely | Leading-zero stripping; ambiguous date formats; duplicate IDs |
| **Info** | Worth noting, no direct downstream breakage | Near-constant columns; unusual cardinality |

---

## Project Structure

```
datascope/
├── loaders/          # Excel and CSV with cell-level type tracking
│   ├── excel.py      # openpyxl-based, preserves per-cell Python types
│   ├── csv_loader.py # Raw string inference (None → int → float → bool → datetime → str)
│   └── base.py       # Extension-based dispatch
├── analyzers/        # Five detectors, each returns list[Finding]
│   ├── type_consistency.py
│   ├── sentinel.py
│   ├── format_check.py
│   └── cardinality.py
├── findings/         # Severity classifier + NL template engine
│   ├── severity.py   # Impact-based classification rules
│   ├── templates.py  # Plain-English templates per finding sub-type
│   ├── composer.py   # Template dispatch
│   └── pipeline.py   # classify → compose → sort
├── reports/
│   └── pdf.py        # Professional PDF with reportlab
└── cli.py            # argparse CLI, pipeline orchestration
```

---

## Requirements

- Python 3.10+
- pandas >= 2.0
- openpyxl >= 3.1
- reportlab >= 4.0
- numpy >= 1.24

---

## License

MIT
