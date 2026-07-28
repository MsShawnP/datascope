
## Serif display sizes — documented deviation

`datascope/reports/html.py` sets its serif display steps as literals rather
than pulling the Lailara type-scale tokens. This is deliberate and stays:

| Selector | Size | DS token | Status |
|---|---|---|---|
| `.title-section h1` | 28px | Section title is 22px; 28px is the Benchmark-value step | **Deviation.** Report title, not a page section header. 22px does not carry a document title at 900px container width. |
| `.summary-number` | 32px | Benchmark value is 28px | **Deviation.** Three summary cards side by side read as the report's headline figures; 28px collapses them into the finding-card hierarchy. |
| `h2` | 18px | Section title is 22px / 18px mobile | **Deviation.** Subordinate to the 28px report title; matches the DS "card / sub-section head" 18–20 role. |

No mobile steps are declared for these — the 640px block resizes `h1` and
`.summary-number` only. The frame's `.ll-*` display classes are not available
here: this generator emits a self-contained HTML file and does not vendor
`lailara-frame.css`.

Revisit only as a deliberate typography pass with the rendered report in front
of you. Do not "fix" these to tokens mechanically.
