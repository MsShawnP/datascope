# Decisions

## 2026-05-15: PyPI distribution name → datascope-dq

`datascope` is taken on PyPI by an ETH Zurich ML tool (Shapley-value data importance scores). Chose `datascope-dq` as the distribution name — short, communicates "data quality." The Python import stays `import datascope`. All install docs, README, and branding reference `pip install datascope-dq`.

Alternatives considered: `datascope-diagnostics` (too verbose), `datascope-cli` (undersells the library use case).

## 2026-05-15: FindingType sub-types promoted to first-class enum values

Promoted LEADING_ZEROS, MIXED_DATES, NEAR_CONSTANT, DUPLICATE_IDS from implicit evidence-key conventions to explicit `FindingType` enum members. Removed the old generic `FORMAT_INCONSISTENCY` and `CARDINALITY_ANOMALY` types.

This eliminated 6 dispatch sites across severity.py, composer.py, and pdf.py that inspected magic dict keys like `"leading_zero_count" in evidence`. New finding types must be added as enum values with corresponding template, severity rule, and PDF label — not smuggled through evidence keys.

## 2026-05-15: PEP 639 license format — drop legacy classifier

Modern setuptools (isolated build env) rejects the `License :: OSI Approved :: MIT License` classifier when `license = "MIT"` is also present. Removed the classifier, keeping only the PEP 639 `license` string field. Future classifiers should not include license entries.
