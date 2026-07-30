# Changelog

All notable changes to datascope are documented here.

## [2.3.3] — 2026-07-30

### Changed
- **Report health assessment** now names the consequence: warning-level findings state that they typically skew joins and aggregations quietly, instead of a generic "address before production" line.
- **Print styles tokenized** to the Lailara palette: report body ink is London-5 (`#0d0d0d`) and summary-card borders are London-85 (`#d9d9d9`) in print, replacing off-palette `#000`/`#ccc`.

## [2.3.2] — 2026-07-27

### Fixed
- **Suspected-duplicate-ID detection** no longer misses duplicates in large ID columns. The uniqueness ratio was rounded to 4 decimals before the `< 1.0` comparison, so a column ≥ ~99.995% unique (e.g. 19,999 distinct out of 20,000) rounded to exactly 1.0 and was silently passed as clean. The gate is now the exact integer test `unique_count < total_count`.
- **Duplicate column headers** are now disambiguated at load time (`amount`, `amount.1`), matching pandas. Previously two columns sharing a header collapsed to one `cell_types` entry while the DataFrame kept both, causing per-column analyzers to crash on a same-named DataFrame — a crash the CLI silently swallowed, so the file was never fully analyzed.
- **Missing-value positions** are now reported by 0-based row position rather than index label. A non-default index (which Parquet can restore, including a datetime index) previously produced wrong positions, and a non-integer index crashed the distribution report. Counts and percentages were always correct; only positional evidence was affected.
- **CSV cell inference** now keeps `inf`, `-inf`, `infinity`, `nan`, and underscore-grouped tokens like `1_000` as strings. `int()`/`float()` accept these Python-specific spellings, so a genuine text or sentinel cell was silently coerced to a number — and `nan` even vanished as a null.

## [2.3.1] — 2026-07-15

### Added
- PDF reports embed the Lailara brand typefaces — Playfair Display (serif) and Source Sans 3 (sans) — instead of falling back to base-14 Helvetica/Times.

### Fixed
- Brand-font TTFs and their OFL licenses are now packaged into the wheel and sdist (`tool.setuptools.package-data`). Previously only `brand_fonts/__init__.py` shipped, so a pip-installed copy could not embed the fonts and fell back to Helvetica; embedding worked only from a source checkout.

## [2.3.0] — 2026-07-07

### Fixed
- **Near-constant detection** now fires on *mode dominance* — when a single value covers ≥95% of non-null rows — instead of low overall uniqueness. This stops legitimate low-cardinality categoricals (e.g. `order_status`, `is_renewal`) from being wrongly flagged. Evidence gains a `dominant_pct` field.
- **Suspected-duplicate-ID detection** now only fires on identifier-like columns: those whose name tokenizes (splitting on non-alphanumerics and camelCase) to an ID word, or whose values are all integer-like. Continuous decimal measures like `revenue` and free-text columns are no longer flagged as ID columns with duplicates.

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
