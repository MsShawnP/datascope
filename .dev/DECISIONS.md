# Decisions

## 2026-05-15: PyPI distribution name → datascope-dq

`datascope` is taken on PyPI by an ETH Zurich ML tool (Shapley-value data importance scores). Chose `datascope-dq` as the distribution name — short, communicates "data quality." The Python import stays `import datascope`. All install docs, README, and branding reference `pip install datascope-dq`.

Alternatives considered: `datascope-diagnostics` (too verbose), `datascope-cli` (undersells the library use case).

## 2026-05-15: FindingType sub-types promoted to first-class enum values

Promoted LEADING_ZEROS, MIXED_DATES, NEAR_CONSTANT, DUPLICATE_IDS from implicit evidence-key conventions to explicit `FindingType` enum members. Removed the old generic `FORMAT_INCONSISTENCY` and `CARDINALITY_ANOMALY` types.

This eliminated 6 dispatch sites across severity.py, composer.py, and pdf.py that inspected magic dict keys like `"leading_zero_count" in evidence`. New finding types must be added as enum values with corresponding template, severity rule, and PDF label — not smuggled through evidence keys.

## 2026-05-15: HTML reports use inline CSS, no Jinja2

HTML report is a single self-contained file with all CSS inlined. No template engine dependency — just f-strings and `html.escape()`. This keeps the dependency footprint minimal (Jinja2 comes via pandas but we don't rely on it) and means the HTML file works offline, in email attachments, or anywhere a browser exists.

## 2026-05-15: Parquet support as optional extra, not core dependency

pyarrow is large (~200MB installed). Making it a core dependency would bloat install for users who only work with CSV/Excel. Instead, it's behind `pip install datascope-dq[parquet]`. The loader raises a clear `ImportError` with install instructions if pyarrow is missing.

## 2026-05-15: PEP 639 license format — drop legacy classifier

Modern setuptools (isolated build env) rejects the `License :: OSI Approved :: MIT License` classifier when `license = "MIT"` is also present. Removed the classifier, keeping only the PEP 639 `license` string field. Future classifiers should not include license entries.

## 2026-05-22: defusedxml removed; openpyxl handles XML safety internally

- **Why:** `defusedxml` was listed as a dependency but never imported. It only works when explicitly imported before XML parsing (monkey-patches stdlib). Modern openpyxl (3.1+) handles XML parsing safely without it. The dependency added install weight with no protection.
- **Scope:** datascope dependency management
- **Do not:** Re-add defusedxml unless datascope starts parsing user-supplied XML outside of openpyxl (e.g., raw lxml usage).

## 2026-05-16: Stay in the file-audit niche; do not compete with pipeline tools

- **Why:** GX owns rules, Pandera owns schemas, Soda owns databases, ydata owns stats. datascope's moat is cell-level detection + professional narrative reports for non-technical readers. Competing on their turf dilutes the positioning.
- **Scope:** All future feature decisions for datascope
- **Do not:** Add custom validation rules, database connectors, statistical profiling, Polars backend, drift detection, or web UI/SaaS
