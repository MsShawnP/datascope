# datascope — Project Audit

Generated: 2026-05-15

---

## Phase 1: Baseline Assessment

### What It Is Today

**datascope v2.0.0** — a Python CLI tool that analyzes Excel/CSV files for hidden data quality issues and produces professional PDF diagnostic reports in plain English.

**Core insight:** Most tools let pandas silently coerce types (485 numbers + 15 strings → all float64, strings become NaN). datascope reads each cell's actual Python type, detects quality issues, and explains them as "assumption vs. reality" findings for non-technical readers.

### By the Numbers

| Metric | Value |
|--------|-------|
| Production code | ~1,620 LOC across 15 files |
| Test code | ~3,450 LOC, 265 test cases |
| Test:code ratio | 2.1:1 |
| Dependencies | 4 runtime (pandas, openpyxl, reportlab, numpy) |
| Python target | 3.10+ |
| Git commits | 23 over 62 days |
| Open issues/PRs | 0 / 0 |
| License | MIT (Shawn, Lailara LLC) |

### Architecture (5 layers)

```
INPUT (Excel/CSV)
  → Loaders (235 LOC) — cell-level type preservation, no silent coercion
  → Analyzers (633 LOC) — 5 detectors: type consistency, sentinels, leading zeros, mixed dates, cardinality
  → Findings (239 LOC) — severity classification + plain-English template composition
  → Reports (605 LOC) — professional PDF via reportlab, color-coded severity cards
  → CLI (205 LOC) — argparse orchestration, stdout summary
OUTPUT (PDF + stdout)
```

### What's Strong

1. **Architecture** — clean layer separation, extensible Finding data model, no monolith
2. **Test coverage** — 265 tests at 2.1:1 ratio; unit + integration + CLI tests
3. **Documentation** — portfolio-grade README, brainstorm/plan/learning docs in docs/
4. **Code quality** — type hints throughout, ruff configured, zero TODO/FIXME/HACK comments
5. **Product thinking** — "assumption vs. reality" framing, non-technical audience focus, severity by downstream impact
6. **Packaging** — proper pyproject.toml, entry point, editable install

### What's Missing or Weak

1. **No CI/CD** — no GitHub Actions; quality gates are manual
2. **No CHANGELOG** — v1→v2 was a major rewrite with no migration record
3. **Legacy scorer.py** — v1 monolith (~31KB) still in root, not archived
4. **Single output format** — PDF only; no Excel/HTML/JSON export
5. **Limited input sources** — Excel and CSV only; no database, no Parquet, no API
6. **No strict mode flag removed** — README git clone URL still says `field-story-scorer.git` but repo renamed to `datascope`
7. **No PyPI publishing** — local install only
8. **generate_sample.py in root** — utility script not in tools/ folder
9. **tools/render_strict_mode_comparison.py** — references v1 strict mode concept, may be stale

### Project Identity

- **Repo:** MsShawnP/datascope (renamed from field-story-scorer)
- **Audience:** Data consultants, developers, business analysts
- **Differentiator:** Cell-level type detection + plain-English diagnostic reports
- **Stage:** v2.0 shipped 2026-05-14, no users yet beyond author

---

## Phase 2: Internal Review

Five parallel reviews: architecture, testing, performance, security, UX/docs. Findings ranked by leverage — what moves the needle most for the least effort.

### Tier 1 — High Leverage (fix before promoting the project)

| # | Finding | Dimension | Why It Matters |
|---|---------|-----------|----------------|
| 1 | **README clone URL points to old repo name** `field-story-scorer.git` | UX | Every new user hits this immediately; the `cd` command also fails |
| 2 | **`samples/README.md` is entirely about v1** — references scorer.py, --strict-types, scoring numbers | UX | New users exploring samples/ get a completely misleading picture |
| 3 | **Missing `defusedxml` dependency** — openpyxl uses stdlib XML parser without it, exposing XML bomb/XXE risk | Security | One-line fix (`defusedxml>=0.7.0`) that closes a real attack vector for a tool that processes untrusted files |
| 4 | **Legacy `scorer.py` (791 LOC) still in root** — confusing, weaker security posture, imported by tools/ | Architecture | Confuses contributors, duplicates entry points, has unescaped user input in reportlab |
| 5 | **`generate_sample.py` references v1 CLI** — prints `python scorer.py --input ...` | UX | Unusable with v2; generates misleading instructions |
| 6 | **Backtick column names render as literal backticks in PDF** | UX | Every finding card in every report has this cosmetic defect — not "plain English" |
| 7 | **Mixed-dates template newlines ignored in PDF** — `\n`-joined list renders as run-on text | UX | Date format breakdown is unreadable in the actual report |

### Tier 2 — Medium Leverage (meaningful improvements)

| # | Finding | Dimension | Why It Matters |
|---|---------|-----------|----------------|
| 8 | **FindingType sub-types dispatched via evidence-key sniffing** — 6 places check magic dict keys | Architecture | Adding a new sub-type requires finding and updating all 6 locations; promote sub-types to first-class enum values |
| 9 | **No CI/CD** — no GitHub Actions, no automated test/lint gates | DevEx | Quality gates are entirely manual; one workflow file closes this |
| 10 | **Full materialization defeats openpyxl read_only=True** — `list(ws.iter_rows())` loads everything at once | Performance | 1M-row file → ~2.4GB RAM; the streaming flag is wasted |
| 11 | **CSV loads entire file into memory twice** — `list(reader)` + `inferred_rows` list | Performance | Same memory problem, compounded by the type inference copy |
| 12 | **CSV datetime inference is O(n × 7 strptime calls)** per non-date cell | Performance | 1M text-string cells → 7M failed strptime calls; regex pre-filter would cut this 10x |
| 13 | **No `--json` / `--format` output flag** | UX | Blocks pipeline integration, CI/CD usage, programmatic consumption |
| 14 | **Analyzer failures swallowed with one-line warning** — no traceback, can produce false-negative reports | UX | A "No issues detected" report when an analyzer actually crashed is dangerous |
| 15 | **No page numbers or running header in PDF** | UX | Multi-page professional deliverable without pagination |
| 16 | **`source_metadata` is untyped `dict[str, Any]`** — keys established by convention across 3 files | Architecture | Adding a new output format requires guessing which keys exist |
| 17 | **`normalize_type` creates cross-analyzer coupling** — sentinel.py and format_check.py import from type_consistency.py | Architecture | Extract to shared utility in analyzers/base.py |
| 18 | **Dependency version ranges fully open, no lock file** | Security | No reproducible builds; `pip audit` not configured |

### Tier 3 — Polish (lower leverage but worth noting)

| # | Finding | Dimension | Why It Matters |
|---|---------|-----------|----------------|
| 19 | **`cell_types` stores one `type` reference per cell** — near-doubles memory vs DataFrame | Performance | Could use run-length encoding or type codes instead |
| 20 | **CLI analyzer failure error path untested** (cli.py:184-187) | Testing | The only error-resilience mechanism in the pipeline has zero test coverage |
| 21 | **CSV `_infer_cell` never tested in isolation** — 6 inference branches, no direct unit tests | Testing | Leading-zero preservation, the tool's differentiating feature, is tested only indirectly |
| 22 | **Composer fallback branches untested** — 3 default cases in template dispatch | Testing | Silent wrong-template selection if a new sub-type is added |
| 23 | **No `--quiet` / `--verbose` flags** | UX | Blocks scripting (quiet) and debugging (verbose/traceback) |
| 24 | **`requirements.txt` duplicates `pyproject.toml`** — invites version drift | DevEx | Use only pyproject.toml; generate requirements.txt if needed |
| 25 | **`pyproject.toml` missing `authors`, `urls`, `readme` fields** | DevEx | Needed for PyPI publishing |
| 26 | **No mypy/pyright configuration** — type hints are documentation-only | DevEx | Extensive type hints exist but are never verified |
| 27 | **`Analyzer` type alias defined but never imported or used** | Architecture | Dead code in analyzers/base.py |
| 28 | **`numpy` listed as dependency but unused by v2 code** | Architecture | Only used by legacy scorer.py and generate_sample.py |
| 29 | **`--sheet` silently ignored for CSV files** | UX | No warning when the flag has no effect |
| 30 | **PDF health assessment doesn't mention total finding count** | UX | 25 info findings → "only informational" with no sense of volume |

### Cross-Cutting Themes

1. **v1 → v2 cleanup is incomplete.** scorer.py, generate_sample.py, samples/README.md, tools/render_strict_mode_comparison.py, and the README clone URL all reference v1 concepts. This is the single highest-leverage batch of fixes.

2. **The architecture is sound but has one structural weakness.** The evidence-key sniffing pattern for sub-type dispatch (FORMAT_INCONSISTENCY and CARDINALITY_ANOMALY) creates a hidden coupling between analyzers and the findings layer. Promoting sub-types to first-class enum values eliminates this.

3. **Performance is fine for the current audience (<10K rows) but has a hard wall.** Full materialization + cell_types doubling + strptime brute-force means the tool falls over around 100K rows. If the target audience ever includes "production data pipeline" users, this needs a streaming rewrite.

4. **Test coverage is genuinely strong (2.1:1 ratio, 265 tests) but has specific blind spots.** The untested paths are exactly the defensive/error-handling code that matters most when things go wrong: analyzer failures, CSV type inference edge cases, composer fallbacks, PDF health assessment branches.

5. **The PDF report has two rendering bugs** (backtick literals, newline collapse) that affect every report generated. These are quick fixes with high visible impact.

---

## Phase 3: Landscape Scan

### Competitive Set (10 tools)

| Tool | Stars | Type | Input | Output | Type Detection | Audience | Pricing |
|------|-------|------|-------|--------|----------------|----------|---------|
| **ydata-profiling** | 13.6k | Library | DataFrame | HTML | Column-level inference | Data scientists | Free |
| **Great Expectations** | 11.5k | Framework | DataFrame/SQL | HTML "Data Docs" | Rule-based (expectations) | Data engineers | Free + Cloud |
| **Pandera** | 4.3k | Library | DataFrame | Exceptions (no report) | Schema-as-code | Engineers | Free |
| **SweetViz** | 3.1k | Library | DataFrame | HTML | Column-level | DS/ML | Free |
| **whylogs** | 2.8k | Library | DataFrame | JSON profiles | Column-level stats | ML engineers | Freemium |
| **Soda Core** | 2.3k | CLI | SQL/databases | Pass/fail + Cloud UI | YAML check rules | Data engineers | Free + $750/mo Cloud |
| **DataPrep** | 2.2k | Library | DataFrame | HTML | Column-level (Dask) | Data scientists | Free |
| **Pointblank** | <1k | Library | DataFrame/SQL | HTML tables | Threshold-based validation | Analysts (newer) | Free |
| **DataProfiler** | 1.6k | Library | CSV/JSON/Parquet | JSON | Column-level + PII | Data/security analysts | Free |
| **Deepchecks** | — | Library | DataFrame | HTML | Column-ratio mixed-type check | ML engineers | Freemium |

### Feature Matrix — Where datascope Sits

| Capability | datascope | ydata-profiling | Great Expectations | Pandera | Soda Core | Pointblank |
|------------|:---------:|:---------------:|:------------------:|:-------:|:---------:|:----------:|
| **Cell-level type detection** | **Yes** | No | No | No | No | No |
| **Excel-native reading** (openpyxl, no pandas coercion) | **Yes** | No | No | No | No | No |
| **Plain-English narrative** | **Yes** | No | Partial (Data Docs) | No | No | Partial |
| **PDF report output** | **Yes** | No | No | No | No | No |
| **Zero-config CLI** (file in → report out) | **Yes** | No (1-liner but library) | No (expectations required) | No (schema required) | No (YAML required) | No (code required) |
| **CSV support** | Yes | Yes (via pandas) | Yes (via pandas) | Yes | Yes (via SQL) | Yes |
| **Statistical profiling** | No | **Yes** | No | No | No | No |
| **Custom validation rules** | No | No | **Yes** | **Yes** | **Yes** | **Yes** |
| **Pipeline integration** | No | Yes | **Yes** | **Yes** | **Yes** | Yes |
| **Database support** | No | No | Yes | No | **Yes** | Yes |
| **Parquet/Arrow support** | No | Yes | Yes | Yes | Yes | Yes |
| **JSON/machine-readable output** | No | Yes | Yes | Yes | Yes | Yes |
| **Large file performance** | Weak (>100K rows) | Weak | Good | **Good** | Good | Good |
| **Polars support** | No | No | No | Yes | No | **Yes** |
| **Community/stars** | New | 13.6k | 11.5k | 4.3k | 2.3k | <1k |

### datascope's Position: What's Better, Worse, Unique, Missing

**Unique (no competitor does this):**
1. **Cell-level type detection** — every other tool uses column-level inference after pandas/SQL coercion. datascope reads each cell's actual Python type via openpyxl before any coercion happens. This is the core technical moat.
2. **"Assumption vs. reality" narrative framing** — no tool produces prose explanations aimed at non-technical readers. The closest (GX Data Docs, Pointblank tables) are validation result tables, not narratives.
3. **Excel-native reading** — every competitor requires loading through pandas first, which is exactly where type coercion destroys the signal datascope detects.
4. **PDF as portable audit artifact** — no competitor outputs PDF. The inspection-report analogy: the artifact is passed to a client who doesn't control the toolchain.

**Better than competitors:**
5. **Zero-config experience** — `datascope file.xlsx` produces a full report. GX requires expectation suites, Pandera requires schemas, Soda requires YAML. The setup cost for datascope is zero.
6. **Non-technical audience targeting** — while competitors target engineers, datascope targets consultants handing reports to clients.

**Worse than competitors:**
7. **No machine-readable output** — every major competitor supports JSON/HTML/programmatic output. datascope has PDF + unstructured stdout only.
8. **No custom validation rules** — can't define domain-specific checks ("price must be positive", "date must be after 2020").
9. **No pipeline integration** — can't embed in CI/CD, dbt, or Airflow workflows without parsing stdout.
10. **No statistical profiling** — no distributions, correlations, missing-value analysis beyond what the 5 analyzers detect.
11. **Performance ceiling** — falls over at ~100K rows due to full materialization and strptime brute-force.
12. **No community** — new project with zero external users/stars.

**Missing (competitors have, datascope doesn't):**
13. **Database/Parquet/Arrow input** — limited to Excel + CSV.
14. **Polars support** — Polars is the growth vector in the Python data ecosystem.
15. **HTML report option** — for web/email embedding.
16. **Drift detection** — comparing two datasets or monitoring over time (whylogs, Soda territory).

### Market Context

**Where the market is going:**
- Pipeline-integrated observability platforms (Monte Carlo, Sifflet, Datafold — VC-funded)
- AI-augmented test generation (GX DraftValidation, DataOps TestGen)
- Validation-as-feature inside frameworks (Pydantic in FastAPI, dbt tests)

**Where the market is NOT going:**
- Standalone CLI tools for one-shot file auditing
- Stakeholder-facing prose reports
- Excel-native anything

**This is the opportunity.** The market is leaving the "consultant analyzes a client's messy Excel file and needs a professional report" use case completely unaddressed. Every tool is moving toward engineers, pipelines, and platforms. datascope occupies an empty niche.

**The risk:** The niche may be empty because it's small. The growth path requires either (a) staying niche but being the definitive tool for data consultants, or (b) adding enough pipeline features (JSON output, CI integration) to serve both audiences.

### Analogies That Clarify Position

- **Building inspection reports** — inspectors don't hand homeowners JSON schemas. They produce written reports. datascope is the building inspector for data files.
- **Spell-checker UX** — surfaces problems inline, in the user's own document, with one-click fixes. No existing tool does this for data files.
- **Rust compiler errors** — the shift toward human-readable, actionable error messages ("expected integer, found string at column B row 14") maps directly onto datascope's narrative approach.

---

## Phase 4: Synthesis & Next Moves

### Strategic Frame

datascope has a **genuine technical moat** (cell-level type detection) and a **genuine product moat** (plain-English narrative for non-technical readers). No competitor combines both. The architecture is sound, the test coverage is strong, and the code quality is portfolio-grade.

But the project can't capitalize on either moat yet because:
1. **v1 artifacts confuse first impressions** — scorer.py, old README URL, stale samples
2. **PDF rendering bugs undermine the "professional report" value prop** — the core product has cosmetic defects
3. **No machine-readable output blocks the bridge audience** — engineers who'd champion datascope in their org can't integrate it
4. **No CI/CD or PyPI hurts credibility** — open-source adoption requires trust signals

The synthesis produces four ranked move categories: **Clean → Polish → Bridge → Grow.**

---

### Move 1: CLEAN — Ship-ready baseline (1-2 sessions)

*Goal: A stranger who finds the repo can install, run, and trust what they see.*

| Task | Internal Finding | Landscape Rationale | Effort |
|------|-----------------|---------------------|--------|
| Fix README clone URL + cd command | Phase 2 #1 | First-touch UX; every competitor has working install instructions | 5 min |
| Rewrite `samples/README.md` for v2 | Phase 2 #2 | Samples are the "try it yourself" onramp | 30 min |
| Delete `scorer.py` from root | Phase 2 #4 | Eliminates confusion, removes weaker security surface | 5 min |
| Update `generate_sample.py` for v2 CLI | Phase 2 #5 | Makes sample generation actually work | 15 min |
| Retire or port `tools/render_strict_mode_comparison.py` | Phase 2 #4 | Last v1 import reference | 15 min |
| Add `defusedxml>=0.7.0` to dependencies | Phase 2 #3 | One-line fix; closes XML bomb vector for a tool processing untrusted files | 2 min |
| Drop `numpy` from dependencies (unused by v2) | Phase 2 #28 | Smaller install footprint, honest dependency list | 2 min |

**Total: ~75 minutes of focused work. Zero architectural risk.**

---

### Move 2: POLISH — The report is the product (1-2 sessions)

*Goal: Every PDF datascope produces is genuinely professional and correct.*

| Task | Internal Finding | Landscape Rationale | Effort |
|------|-----------------|---------------------|--------|
| Fix backtick literals in PDF templates | Phase 2 #6 | The report is datascope's differentiator; literal backticks aren't "plain English" | 30 min |
| Fix newline collapse in mixed-dates template | Phase 2 #7 | Date format breakdown is unreadable as run-on text | 20 min |
| Add page numbers + running header to PDF | Phase 2 #15 | Every competitor's HTML report has navigation; PDF needs pagination | 45 min |
| Fix PDF health assessment to mention total count | Phase 2 #30 | "Only informational" with 25 findings buries the signal | 15 min |
| Regenerate v2 sample outputs in `samples/output/` | Phase 1 gap | Current samples are v1 artifacts | 15 min |

**Total: ~2 hours. These are the changes users actually see.**

The landscape confirms this priority: datascope's unique position is the **report**. ydata-profiling has better stats. GX has better rules. Pandera has better schemas. But none of them produce a report you'd hand to a non-technical client. If the PDF has cosmetic bugs, the entire value proposition is undermined.

---

### Move 3: BRIDGE — Serve both audiences (2-3 sessions)

*Goal: Engineers can integrate datascope into pipelines; consultants still get their PDF.*

| Task | Internal Finding | Landscape Rationale | Effort |
|------|-----------------|---------------------|--------|
| Add `--format json` output flag | Phase 2 #13 | Every competitor has machine-readable output; this is datascope's biggest functional gap | 2-3 hr |
| Add `--verbose` / `--quiet` flags | Phase 2 #23 | `--quiet` enables scripting (exit code only); `--verbose` enables debugging | 1 hr |
| Add GitHub Actions CI (pytest + ruff) | Phase 2 #9 | Table-stakes trust signal for open-source adoption | 30 min |
| Promote FindingType sub-types to first-class enums | Phase 2 #8 | Eliminates evidence-key sniffing in 6 locations; unblocks adding new analyzers | 2 hr |
| Type `source_metadata` as TypedDict | Phase 2 #16 | Unblocks adding new output formats without guessing keys | 30 min |
| Complete `pyproject.toml` metadata (authors, urls, readme) | Phase 2 #25 | Required for PyPI publishing | 10 min |
| Publish to PyPI | Phase 1 gap | `pip install datascope` is the expected install path; git clone is friction | 1 hr |

**Why `--format json` is the single highest-leverage feature:**
- It's the bridge between datascope's consultant audience and the engineer audience
- Engineers who discover datascope via PyPI can plug it into CI/CD: `datascope data.csv --format json | jq '.findings[] | select(.severity == "CRITICAL")'`
- JSON output is the prerequisite for GitHub Actions integration, Slack alerts, dashboard embedding
- It costs 2-3 hours and doubles the addressable audience

---

### Move 4: GROW — Expand the moat (future sessions)

*Goal: Make datascope the definitive tool for its niche, then expand.*

| Task | Landscape Rationale | Effort |
|------|---------------------|--------|
| **Add HTML report option** | Email-embeddable; web-viewable; complements PDF for different delivery contexts | 3-4 hr |
| **Add `--max-rows` / size guard** | Prevents OOM on large files; sets user expectations honestly | 1 hr |
| **Regex pre-filter for CSV datetime inference** | 10x speedup on text-heavy CSVs; moves the performance wall from 100K to 1M rows | 1 hr |
| **Add Parquet/CSV-from-stdin input** | Parquet is the growth vector; stdin enables piping from other tools | 2-3 hr |
| **Add a sixth analyzer: missing-value patterns** | Gap vs. ydata-profiling; "15% of rows have no email" is a finding consultants care about | 2-3 hr |
| **Add annotated Excel output** — highlight problem cells in the source file | The "spell-checker UX" analogy; no competitor does this; huge differentiation | 4-6 hr |
| **Stream-process loaders** | Eliminates the 100K-row memory wall entirely | 4-6 hr |
| **Lock file + `pip audit` in CI** | Reproducible builds + vulnerability scanning | 30 min |

The annotated Excel output is the **long-term differentiator**. No tool in the landscape highlights problem cells in the user's own file. Combined with the PDF diagnostic report, this creates a two-artifact deliverable: "here's your file with problems highlighted, and here's the report explaining what each problem means." That's the building-inspection analogy made concrete.

---

### Strategic Summary

```
Now          Soon              Next               Later
─────────────────────────────────────────────────────────
CLEAN        POLISH            BRIDGE              GROW
v1 artifacts PDF rendering     --format json       HTML reports
defusedxml   page numbers      CI/CD               Parquet input
scorer.py    sample outputs    PyPI publish        Annotated Excel
README URL   health text       enum sub-types      Stream loaders
                               --verbose/--quiet   Missing-value analyzer
```

**The thesis:** datascope's moat is the combination of cell-level detection and professional narrative output. Clean the repo (Move 1), make the report flawless (Move 2), then add JSON output to bridge the engineer audience (Move 3). Everything after that deepens the moat or expands the audience.

**What NOT to build:**
- Custom validation rules (GX/Pandera own this; don't compete on their turf)
- Statistical profiling (ydata-profiling owns this; datascope finds *problems*, not *statistics*)
- Database connectivity (Soda owns this; stay in the file-auditing lane)
- Drift detection (whylogs owns this; datascope is point-in-time, not longitudinal)
- Web UI / SaaS (premature; the CLI + report is the right form factor for now)
