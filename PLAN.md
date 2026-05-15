# datascope — Improvement Plan

Derived from full project audit (2026-05-15). See AUDIT.md for rationale.

Tier: Medium
Current focus: Moves 1-3 complete. Move 4 (GROW) is next.

---

## Move 1: CLEAN — Ship-ready baseline

Goal: A stranger who finds the repo can install, run, and trust what they see.

### 1A: Fix README install URL ✓
- Depends on: none
- Change `field-story-scorer.git` → `datascope.git` and `cd field-story-scorer` → `cd datascope` in README.md:27-28
- Done when: `grep -c "field-story-scorer" README.md` returns 0

### 1B: Add defusedxml, drop numpy from dependencies ✓
- Depends on: none
- Add `defusedxml>=0.7.0` to pyproject.toml `[project.dependencies]` and requirements.txt
- Remove `numpy>=1.24.0` from both files (v2 code never imports numpy)
- Done when: `pip install -e .` succeeds; `python -c "import defusedxml"` succeeds; `grep numpy pyproject.toml` returns nothing

### 1C: Delete scorer.py and update its dependents ✓
- Depends on: none
- Delete `scorer.py` from repo root
- Update `tools/render_strict_mode_comparison.py`: either delete it (if stale) or port the `from scorer import analyze, load_strict` to v2 APIs (`from datascope.loaders import load_file` + v2 analyzer pipeline)
- Done when: `grep -r "from scorer" .` returns nothing; `python -m pytest` still passes

### 1D: Update generate_sample.py for v2 ✓
- Depends on: 1C (scorer.py must be gone so old instructions don't work)
- Change print statements at lines 87-88 from `python scorer.py --input ...` to `datascope <file> --output-dir ...`
- Move to `tools/` directory for consistency (optional, confirm with user)
- Done when: `python generate_sample.py` prints v2 CLI commands; no reference to `scorer.py` in file

### 1E: Rewrite samples/README.md for v2 ✓
- Depends on: 1C, 1D (need v1 artifacts gone before rewriting the guide)
- Replace entire file: describe v2 diagnostic reports, reference `datascope` CLI, update output file names, remove scoring numbers and --strict-types references
- Done when: `grep -c "scorer\|strict-types\|field-story-scorer\|field_report" samples/README.md` returns 0; file describes v2 outputs and commands

### 1F: Integration verify ✓
- Depends on: 1A-1E all complete
- Run full test suite: `python -m pytest`
- Run tool end-to-end: `datascope samples/input/sample_mixed_types.xlsx --output-dir /tmp/test`
- Verify PDF is produced and stdout summary prints correctly
- Done when: all tests pass; PDF exists and opens; no stderr warnings about missing imports

---

## Move 2: POLISH — The report is the product

Goal: Every PDF datascope produces is genuinely professional and correct.

### 2A: Fix backtick literals in templates ✓
- Depends on: none
- In `datascope/findings/templates.py`, replace backtick-wrapped field names (e.g., `` f"Column `{field_name}`" ``) with either bare names or bold tags reportlab understands (`<b>{field_name}</b>`)
- ~30 occurrences across 6 template functions
- Done when: `grep -c '`' datascope/findings/templates.py` returns 0 (for backtick-wrapped names); generate a test PDF and visually confirm field names render without literal backtick characters

### 2B: Fix newline collapse in mixed-dates template ✓
- Depends on: none
- In `datascope/findings/templates.py:224-225`, replace `"\n".join(format_parts)` with `"<br/>".join(format_parts)` so reportlab Paragraph renders line breaks
- Verify _safe() in pdf.py doesn't escape `<br/>` tags (it escapes `<` and `>` — need to handle this)
- Done when: generate a PDF from sample_mixed_types.xlsx; the date format breakdown in the mixed-dates finding renders as a vertical list, not run-on text

### 2C: Add page numbers and running header to PDF ✓
- Depends on: none
- In `datascope/reports/pdf.py`, add an `onLaterPages` callback to `SimpleDocTemplate` that renders "datascope diagnostic — {filename}" as a header and "Page N" as a footer
- Done when: generate a multi-page PDF; every page after the title has a header and page number

### 2D: Fix health assessment total count ✓
- Depends on: none
- In `datascope/reports/pdf.py:244-278`, update health assessment text branches to include total finding count (e.g., "25 informational observations were found" instead of "Only informational observations were found")
- Done when: test with a dataset that produces only info findings; health assessment text includes the count

### 2E: Regenerate v2 sample outputs ✓
- Depends on: 2A, 2B, 2C, 2D (want polished PDF before committing samples)
- Run `datascope samples/input/sample_mixed_types.xlsx --output-dir samples/output/` and `datascope samples/input/sample_sales.xlsx --output-dir samples/output/`
- Delete old v1 output files (`*_field_report.*`, `*_field_report_strict.*`)
- Update screenshots if applicable
- Done when: `samples/output/` contains only v2 diagnostic PDFs; no v1 artifacts remain

---

## Move 3: BRIDGE — Serve both audiences

Goal: Engineers can integrate datascope into pipelines; consultants still get their PDF.

### 3A: Promote FindingType sub-types to first-class enums ✓
- Depends on: none
- Add `LEADING_ZEROS`, `MIXED_DATES`, `NEAR_CONSTANT`, `DUPLICATE_IDS` to `FindingType` enum in models.py
- Update analyzers to emit the specific type (format_check.py, cardinality.py)
- Remove evidence-key sniffing in severity.py (~4 helper functions + 2 branches) and composer.py (~2 branches)
- Update test assertions that reference the old generic types
- Done when: `grep -c "leading_zero_count.*in.*evidence\|date_formats.*in.*evidence\|near_constant\|suspected.*duplicate" datascope/findings/severity.py datascope/findings/composer.py` returns 0; all tests pass

### 3B: Type source_metadata as TypedDict ✓
- Depends on: none
- Add `SourceMetadata = TypedDict(...)` in models.py with keys: filename, sheet, row_count, column_count
- Update `LoaderResult.source_metadata` type annotation from `dict[str, Any]` to `SourceMetadata`
- Update loaders and pdf.py to use typed access
- Done when: `mypy datascope/models.py` passes (or `pyright` equivalent); no `dict[str, Any]` for source_metadata

### 3C: Add `--format json` output flag ✓
- Depends on: 3A (clean enum makes JSON serialization straightforward)
- Add `--format {pdf,json,both}` argument to cli.py (default: pdf for backward compat)
- JSON schema: `{"source": {...metadata}, "findings": [{severity, finding_type, field_name, assumption, reality, impact, fix, prevention, evidence}], "summary": {critical, warning, info, total}}`
- When format=json, write to `<stem>_diagnostic.json` alongside or instead of PDF
- Done when: `datascope samples/input/sample_mixed_types.xlsx --format json | python -m json.tool` produces valid JSON with all finding fields populated

### 3D: Add `--verbose` / `--quiet` flags ✓
- Depends on: none
- `--quiet`: suppress stdout summary, exit code only (0 = no critical, 1 = has critical findings)
- `--verbose`: print full traceback on analyzer failures instead of one-line warning
- Done when: `datascope file.xlsx --quiet` produces no stdout; `datascope file.xlsx --verbose` with a patched-to-fail analyzer shows full traceback

### 3E: Add GitHub Actions CI workflow ✓
- Depends on: none
- Create `.github/workflows/ci.yml`: pytest + ruff check on push/PR, Python 3.10-3.12 matrix
- Done when: push to a branch triggers CI; green check on passing tests

### 3F: Complete pyproject.toml metadata ✓
- Depends on: none
- Add `authors`, `urls` (homepage, repository, issues), `readme = "README.md"` fields
- Done when: `python -m build` produces a wheel whose metadata includes author, homepage URL, and rendered README

### 3G: Publish to PyPI ✓
- Depends on: 3E, 3F (CI must be green; metadata must be complete)
- Register `datascope` on PyPI (check name availability first — may need `datascope-dq` or similar)
- Add GitHub Actions publish workflow (on tag push)
- Done when: `pip install datascope` (or chosen name) from a fresh venv installs and runs successfully

---

## Move 4: GROW — Expand the moat (future)

Goal: Deepen the technical moat and expand the addressable audience.

### 4A: Add `--max-rows` / file size guard ✓
- Depends on: none
- After loading, check `row_count * column_count`; warn if > 500K cells; abort if > 5M cells (configurable via `--max-rows`)
- Done when: `datascope huge_file.csv` prints a warning at 500K cells and aborts at 5M with a clear message

### 4B: Regex pre-filter for CSV datetime inference
- Depends on: none
- Port `_DATE_LIKE_RE` from format_check.py:139 to csv_loader.py's `_infer_cell`; skip strptime loop if regex doesn't match
- Done when: benchmark on a 100K-row CSV of text strings shows >5x speedup vs. current; all existing tests pass

### 4C: Add HTML report option ✓
- Depends on: 3A (clean enum types), 3C (JSON output as data source for HTML)
- New `datascope/reports/html.py` — Jinja2 template rendering the same finding data as the PDF
- Wire to `--format html` in cli.py
- Done when: `datascope file.xlsx --format html` produces a self-contained HTML file that opens in browser with styled finding cards

### 4D: Add missing-value pattern analyzer ✓
- Depends on: 3A (new FindingType enum value: `MISSING_VALUE_PATTERN`)
- New analyzer in `datascope/analyzers/missing_values.py`
- Detects: columns with >N% nulls, row-level patterns (all nulls in a row = likely empty row), correlated missingness
- Template in templates.py, severity rule in severity.py
- Done when: running on a dataset with a 40%-null column produces a finding with assumption/reality/impact text

### 4E: Add annotated Excel output
- Depends on: none (but benefits from 3A for clean finding types)
- New `datascope/reports/annotated_excel.py` — copies input file, highlights problem cells with conditional formatting, adds a "Findings" sheet
- Wire to `--format annotated-excel` in cli.py
- Done when: `datascope file.xlsx --format annotated-excel` produces a copy of the input with problem cells highlighted in red/amber/blue

### 4F: Add Parquet input support
- Depends on: none
- New `datascope/loaders/parquet.py` — reads via pyarrow, maps Arrow types to Python types for cell_types
- Add `pyarrow` as optional dependency (`pip install datascope[parquet]`)
- Done when: `datascope data.parquet` produces a diagnostic report; cell_types correctly maps Arrow schema types

### 4G: Stream-process loaders
- Depends on: 4A (size guard provides fallback for unsupported streaming cases)
- Refactor excel.py and csv_loader.py to build DataFrame + cell_types in a single streaming pass without intermediate `list()` materialization
- Done when: benchmark on a 500K-row file shows <500MB peak memory (vs. current ~1.5GB); all existing tests pass

### 4H: pip audit in CI ✓
- Depends on: 3E (CI must exist)
- Generate `requirements.lock` via `pip-compile` or `uv pip compile`
- Add `pip audit` step to CI workflow
- Done when: `pip install -r requirements.lock` produces identical installs; CI fails on known-vulnerable dependencies
