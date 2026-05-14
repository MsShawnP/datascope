# Samples

Real outputs from `field-story-scorer`, committed so you can see what the tool produces without running it yourself. The strict-mode comparison on `sample_mixed_types.xlsx` is the headline — it's the clearest demonstration of what `--strict-types` actually catches.

## Layout

```
samples/
├── input/                  # Synthetic source files (regenerate with `python generate_sample.py`)
│   ├── sample_sales.xlsx
│   └── sample_mixed_types.xlsx
└── output/                 # Reports produced by scorer.py
    ├── sample_sales_field_report.{xlsx,pdf}
    ├── sample_mixed_types_field_report.{xlsx,pdf}
    ├── sample_mixed_types_field_report_strict.{xlsx,pdf}
    └── screenshots/        # Rendered previews of the Excel/PDF reports
```

## Inputs

| File | Rows × Cols | What it exercises |
|---|---|---|
| [sample_sales.xlsx](input/sample_sales.xlsx) | 500 × 15 | A varied but clean dataset — categorical, numeric, boolean, datetime-as-string, sparse, and constant columns. Shows the full range of field types the scorer classifies. |
| [sample_mixed_types.xlsx](input/sample_mixed_types.xlsx) | 200 × 4 | Engineered to demonstrate `--strict-types`. The `revenue_mixed` column has 185 floats and 15 cells containing the literal string `"N/A"` — pandas silently coerces these to `NaN` on load. |

## Outputs

| Output file | Source command | What it demonstrates |
|---|---|---|
| [sample_sales_field_report.xlsx](output/sample_sales_field_report.xlsx) | `scorer.py --input samples/input/sample_sales.xlsx` | Full Excel report on the clean dataset — all four tabs (Field Rankings, Field Profiles, Chart Recommendations, Correlation Matrix) with conditional formatting and data bars. |
| [sample_sales_field_report.pdf](output/sample_sales_field_report.pdf) | (same as above) | PDF version of the same report — landscape, color-coded score cells. |
| [sample_mixed_types_field_report.xlsx](output/sample_mixed_types_field_report.xlsx) | `scorer.py --input samples/input/sample_mixed_types.xlsx` | **Standard mode.** `revenue_mixed` scores **0.9775** and is classified as `numeric_continuous` — the 15 string cells are invisible. This is the false-positive story. |
| [sample_mixed_types_field_report.pdf](output/sample_mixed_types_field_report.pdf) | (same as above) | PDF of the standard-mode mixed-types run. |
| [sample_mixed_types_field_report_strict.xlsx](output/sample_mixed_types_field_report_strict.xlsx) | `scorer.py --input samples/input/sample_mixed_types.xlsx --strict-types` | **Strict mode.** Same input. `revenue_mixed` now scores **0.9708** (type contamination shows up in `type_consistency` 0.925 vs 1.0), and the new `type_mix` column shows `[numeric:185, str:15]`. The string contamination is exposed. |
| [sample_mixed_types_field_report_strict.pdf](output/sample_mixed_types_field_report_strict.pdf) | (same as above) | PDF of the strict-mode run — open this side-by-side with the non-strict PDF and look at the `type_mix` column. |

## The strict-mode story, in one line

| Mode | Score | Type | Type breakdown |
|---|---|---|---|
| Standard | 0.9775 | `numeric_continuous` | *(column not present — pandas inferred away)* |
| `--strict-types` | 0.9708 | `numeric_continuous` | `numeric:185, str:15` |

Same file. Same column. Standard mode says "ship it" with no visibility into the cells. Strict mode keeps the score honest (only `type_consistency` is dinged, because the other dimensions still see legitimate numeric values for 92.5% of rows) and surfaces the new `type_mix` column so you can see exactly which cells are off — "this column has 15 sentinel strings, go talk to whoever exported it."

## Regenerating

```bash
python generate_sample.py                                                              # rewrite samples/input/
python scorer.py --input samples/input/sample_sales.xlsx        --output-dir samples/output/
python scorer.py --input samples/input/sample_mixed_types.xlsx  --output-dir samples/output/
python scorer.py --input samples/input/sample_mixed_types.xlsx  --output-dir samples/output/ --strict-types
```

The generator uses a fixed seed (`42`) so regenerated inputs are byte-stable. Outputs may differ slightly across `openpyxl` / `reportlab` versions.
