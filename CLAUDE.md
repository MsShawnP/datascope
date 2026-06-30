# datascope

Data quality diagnostics for tabular datasets. Surfaces hidden problems (mixed types, sentinel values, leading zeros, mixed dates, near-constant columns, duplicate IDs, missing-value patterns) and generates professional narrative reports in plain English.

**Stack:** Python 3.10+, pandas, openpyxl, reportlab. Published to PyPI as `datascope-dq`.

**Input formats:** .xlsx, .csv, .parquet (pyarrow optional)
**Output formats:** PDF, HTML, JSON, annotated Excel

**Architecture:** Loader -> Analyzers (7) -> Severity classifier -> NL composer -> Report generators. Each stage is independent; findings flow through a pipeline in `findings/pipeline.py`.

**Key conventions:**
- Severity is assigned only in `findings/severity.py`, never in analyzers
- Narrative text comes only from `findings/templates.py`, never from report generators
- Shared colors/labels live in `reports/_palette.py` (single source of truth)
- All report generators follow the Lailara Design System

---

## Design System

Read `../lailara-design-system/LAILARA_DESIGN_SYSTEM.md` before any visual work — colors, typography, layout, components, charts, voice, interactions. It is the single source of truth.

---

Never write secrets, tokens, or passwords into tracked files, READMEs, or commit messages — use environment variables and secret stores only.
