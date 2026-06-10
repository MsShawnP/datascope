# Changelog

All notable changes to datascope are documented here.

## [2.2.1] — 2026-06-10

### Fixed
- README image and file links converted to absolute URLs for correct PyPI rendering

## [2.2.0] — 2026-05-15

### Added
- Parquet input support (`pip install datascope-dq[parquet]`)
- HTML report output (`--format html`)
- Annotated Excel output (`--format annotated-excel`) — highlights problem cells in the source file
- Missing-value pattern analyzer (detects high null rates and distribution)
- `--max-rows` safety guard for large datasets
- `pip-audit` step in CI workflow
- Regex pre-filter for CSV datetime inference (10x speedup on text-heavy files)

### Changed
- Report branding: PDF title page, versioned footers, HTML favicon and meta tags
- JSON output includes `generator` field for provenance

## [2.1.0] — 2026-05-15

### Added
- JSON output format (`--format json`) for pipeline integration
- `--verbose` and `--quiet` CLI flags
- GitHub Actions CI (pytest + ruff + pip-audit)
- PyPI publishing as `datascope-dq`
- `--format both` for PDF + JSON together

### Changed
- Promoted FindingType sub-types to first-class enum values
- Complete `pyproject.toml` metadata for PyPI

## [2.0.0] — 2026-05-14

### Added
- Complete v2 rewrite: cell-level type detection architecture
- 5 analyzers: type consistency, sentinels, leading zeros, mixed dates, cardinality
- Severity classification by downstream impact (Critical / Warning / Info)
- Plain-English narrative templates ("assumption vs. reality" framing)
- Professional PDF report via reportlab
- CSV loader with raw-string type inference
- Excel loader via openpyxl with per-cell type preservation

### Removed
- v1 scoring system (numeric scores replaced by severity + narrative)
- `scorer.py` monolith
- `--strict-types` flag (cell-level detection is always on)

## [1.0.0] — 2026-03-13

Initial release as "field-story-scorer." Single-file tool that scored data quality on a numeric scale. Excel-only input, landscape PDF output.
