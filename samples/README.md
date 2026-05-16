# Samples

Real outputs from datascope, committed so you can see what the tool produces without running it yourself.

## Layout

```
samples/
├── input/                  # Synthetic source files (regenerate with `python generate_sample.py`)
│   ├── sample_sales.xlsx
│   └── sample_mixed_types.xlsx
└── output/                 # Diagnostic reports produced by datascope
    ├── sample_sales_diagnostic.pdf
    ├── sample_sales_diagnostic.html
    ├── sample_mixed_types_diagnostic.pdf
    ├── sample_mixed_types_diagnostic.html
    └── sample_mixed_types_annotated.xlsx
```

## Inputs

| File | Rows × Cols | What it exercises |
|---|---|---|
| [sample_sales.xlsx](input/sample_sales.xlsx) | 500 × 15 | A varied but clean dataset — categorical, numeric, boolean, datetime-as-string, sparse, and constant columns. Shows the full range of field types datascope classifies. |
| [sample_mixed_types.xlsx](input/sample_mixed_types.xlsx) | 200 × 4 | Demonstrates cell-level type detection. The `revenue_mixed` column has 185 floats and 15 cells containing the literal string `"N/A"` — pandas silently coerces these to `NaN` on load, but datascope reads each cell's actual type and flags the inconsistency. |

## Outputs

Each input file produces diagnostic reports in multiple formats:

- **PDF** — professional report with executive summary, severity-coded finding cards, and field inventory
- **HTML** — self-contained web page with the same structure (open in any browser)
- **Annotated Excel** — source data with problem columns highlighted + a Findings summary sheet

## Regenerating

```bash
python generate_sample.py                                                  # rewrite samples/input/
datascope samples/input/sample_sales.xlsx       --output-dir samples/output/
datascope samples/input/sample_mixed_types.xlsx --output-dir samples/output/
```

The generator uses a fixed seed (`42`) so regenerated inputs are byte-stable. Report formatting may differ slightly across `reportlab` versions.
