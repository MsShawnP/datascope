---
title: Cell-Level Type Preservation for Data Quality Diagnostics
date: 2026-05-14
category: architecture-patterns
module: datascope
problem_type: architecture_pattern
component: tooling
severity: high
applies_when:
  - "Reading tabular data (Excel, CSV) where downstream analyzers need per-cell type information"
  - "Building a data quality tool that must detect mixed types, sentinel values, or format inconsistencies"
  - "Ingesting data from sources you do not control and cannot guarantee are well-formed"
symptoms:
  - "Leading-zero strings silently coerced to integers by CSV loader, making the leading-zero detector blind"
  - "Mixed-type columns collapsed to float64; minority-type cells become NaN with no warning"
  - "Quality metrics report 0 issues on columns that have real problems because evidence was erased at load time"
tags:
  - data-quality
  - type-preservation
  - openpyxl
  - pandas
  - pipeline-architecture
  - cell-level-types
---

# Cell-Level Type Preservation for Data Quality Diagnostics

## Context

Most data tools -- pandas, SQL engines, Excel -- make a unilateral type-coercion decision at load time. A column containing 485 integers and 15 free-text values becomes `float64`: the strings become `NaN`, and every downstream aggregation is quietly wrong by whatever fraction those 15 cells represent. The data appears clean; the damage is invisible.

The root tension is that type coercion is convenient (downstream code gets predictable dtypes) but lossy (the coercion decision is irreversible and silent). Once a column is `float64`, there is no way to reconstruct that 15 of those values were originally the string `"TBD"`. The tool that could detect that inconsistency needs the original type information -- and it has been destroyed.

This insight -- that strict-types detection (what pandas silently coerces) is the genuinely novel nucleus of a data quality tool -- drove the datascope v2 architecture. (auto memory [claude])

## Guidance

### Carry a parallel cell-type structure alongside the DataFrame

Instead of letting the loader collapse types into a single dtype, read each cell's actual Python type and store it in a parallel mapping that travels with the DataFrame for the rest of the pipeline.

```python
@dataclass
class LoaderResult:
    dataframe: pd.DataFrame                    # dtype=object throughout -- no coercion
    cell_types: dict[str, list[type]]          # column -> [type per row]
    source_metadata: dict[str, Any]
```

The DataFrame is kept as `dtype=object`. The `cell_types` dict holds the ground truth. Analyzers inspect `cell_types` directly rather than inferring type from the array's dtype.

**Excel loader** -- openpyxl gives you cell values with Python types already attached:

```python
wb = load_workbook(path, data_only=True, read_only=True)
rows = list(ws.iter_rows(values_only=True))
n_cols = len(headers)
data = [list(r) + [None] * max(0, n_cols - len(r)) for r in rows[1:]]  # pad jagged rows
for col_idx, col_name in enumerate(headers):
    cell_types[col_name] = [type(row[col_idx]) for row in data]
```

**CSV loader** needs an explicit inference pipeline since everything arrives as a string:

```python
def _infer_cell(raw: str) -> object:
    stripped = raw.strip()
    if not stripped:
        return None

    # Leading-zero guard MUST come before int() -- "00123" must stay str
    if len(stripped) > 1 and stripped[0] == "0" and stripped.isdigit():
        return stripped

    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        pass
    # ... bool, datetime, fallthrough to str
    return stripped
```

The early return for leading-zero digit strings is load-bearing for the leading-zero analyzer. If `_infer_cell()` converts `"00123"` to `int(123)` first, the type information needed for detection is gone before any analyzer sees it.

### Normalize types at the analysis layer, not the load layer

openpyxl reports `1.0` as `float` even when Excel renders it as an integer. Normalizing at load time would produce false positives. Instead, normalize at the point of use:

```python
def normalize_type(t: type) -> str:
    if t in (int, float):
        return "numeric"
    if t is type(None):
        return "null"
    return t.__name__
```

The raw `int`/`float` distinction is preserved in `cell_types` for any analyzer that needs it (the format checker uses it). The type_consistency analyzer collapses the distinction because the semantics it cares about -- numeric vs. non-numeric -- are unaffected by the int/float split.

### Express severity by downstream impact, not by frequency

A column with 15 sentinel values in 500 rows (3%) is CRITICAL -- not because 3% sounds alarming but because those 15 values become `NaN` silently, and every mean, sum, or join key that touches that column is wrong.

```
CRITICAL  -- silent data loss: values become NaN, calculations are skewed
WARNING   -- key mismatches: joins drop rows, filters return wrong sets
INFO      -- no direct breakage: aesthetic or documentation concern
```

### Frame every finding as assumption vs. reality

The "assumption vs. reality" frame makes the consequence explicit without requiring the reader to infer it:

```
Assumption: Column "revenue" is numeric.
Reality:    15 of 500 values are non-numeric text.
Impact:     Pandas coerces these to NaN. Every sum and mean on this column
            is computed on 485 rows, not 500, with no error raised.
Fix:        Replace non-numeric entries with 0 or null before loading.
```

This structure works for non-technical readers because it answers the only question that matters: "what will break?"

## Why This Matters

**The bug that illustrates the architecture's central challenge** occurred in the CSV loader: `_infer_cell()` converted `"00123"` to `int(123)` before returning, which meant the leading-zero analyzer never had the data it needed. The bug was invisible in unit tests because the test asserted on the DataFrame value (which looked fine as `123`) rather than on the cell type.

This is the canonical failure mode for type-preserving pipelines: if any layer in the pipeline makes an irreversible coercion, every downstream layer that depends on the original type information silently degrades. The pipeline is only as strong as its most aggressive normalizer.

The same failure mode appeared in the Excel loader with jagged rows: `row[col_idx]` without a bounds check crashed on sheets where some rows had fewer columns than the header. The guard (padding to header width) prevents a loader crash from making an entire file's type information unavailable.

**Severity-by-frequency is the wrong heuristic** because it conflates prevalence with consequence. A 0.1% sentinel rate in a 10,000-row transaction log means 10 records silently disappear from every report. A 40% duplicate rate in a lookup table might be perfectly valid if the table is intentionally denormalized.

## When to Apply

- You are reading structured data (CSV, Excel, database dump) from a source you do not control and cannot guarantee is well-formed
- You need to detect type inconsistencies -- mixed numeric/text, sentinel values masquerading as nulls, format variation within a column -- before handing data to downstream consumers
- You are building a data quality tool, an ingestion validator, or an ETL auditor where "coerce and hope" is not an acceptable strategy
- You are producing findings for a non-technical audience and need them to be actionable without a statistics background

This pattern is unnecessary overhead when you fully control the data source and can enforce a schema at write time. It is essential when the data source is a human-edited spreadsheet, a third-party export, or any system where the schema is enforced by convention rather than constraint.

## Examples

**Before (standard pandas load -- type information lost immediately):**

```python
df = pd.read_csv("data.csv")
# df["id"].dtype is float64
# The 15 rows that contained "TBD" are now NaN
# No record remains of what they originally contained
```

**After (datascope load -- type information preserved in parallel):**

```python
result = load("data.csv")
# result.dataframe["id"].dtype is object
# result.cell_types["id"] == [int, int, ..., str, str, ..., int]
# The 15 str entries are exactly locatable; their original values are intact
```

**The leading-zero bug as a before/after for pipeline discipline:**

```python
# WRONG -- destroys the type information the leading-zero analyzer needs
def _infer_cell(raw):
    try:
        return int(raw)          # "00123" -> 123 -- leading zero gone
    except ValueError:
        pass
    return raw

# RIGHT -- early return preserves the string form for the analyzer
def _infer_cell(raw):
    if raw.isdigit() and len(raw) > 1 and raw[0] == "0":
        return raw               # "00123" stays "00123" -- analyzer can see it
    try:
        return int(raw)
    except ValueError:
        pass
    return raw
```

The rule this encodes: **every layer in a type-preserving pipeline must ask "does my transformation destroy information a downstream layer needs?" before applying it.**

## Related

- Origin requirements: `docs/brainstorms/2026-05-14-data-quality-diagnostic-v2-requirements.md`
- Implementation plan: `docs/plans/2026-05-14-001-feat-data-quality-diagnostic-v2-plan.md`
- The `load_strict()` function in the legacy scorer was the technical nucleus that proved cell-level type reading works; datascope v2 generalized it into a modular architecture
