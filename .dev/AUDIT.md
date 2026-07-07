# datascope — Project Audit (Round 2)

**Purpose:** Pre-launch readiness for sharing with prospective clients (C-suite, operations).
**Date:** 2026-05-16

---

## Phase 1: Baseline Assessment

### What Was Intended

A portfolio tool to show how clean or dirty a dataset is — built early in the author's solo dev journey, originally via Claude Chat before adopting a structured workflow.

### What Exists Today

**datascope v2.2.0** — a Python CLI tool that analyzes tabular data (CSV, Excel, Parquet) for hidden data quality issues and produces professional diagnostic reports in plain English. Published on PyPI as `datascope-dq`.

The tool works end-to-end. It reads each cell's actual type (bypassing pandas coercion), detects quality issues, classifies severity by downstream impact, and outputs reports in 5 formats (PDF, JSON, HTML, annotated Excel, PDF+JSON).

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Core deps | pandas, openpyxl, reportlab, defusedxml |
| Optional deps | pyarrow (Parquet support) |
| Dev tools | pytest, ruff |
| CI/CD | GitHub Actions (test + lint + pip-audit + publish) |
| Package | PyPI (`datascope-dq`) |

### Project Health Indicators

| Metric | Value |
|--------|-------|
| Production code | ~3,360 LOC across 20 files |
| Test code | ~3,620 LOC, 283 test cases |
| Test:code ratio | 1.08:1 |
| Dependencies | 4 runtime + 1 optional |
| Git commits | 45 over 64 days |
| Contributors | 1 (+ Claude assist) |
| Activity | Active — last commit 2026-05-15 |
| Documentation | README, samples, brainstorm/plan docs |
| Open issues/PRs | 0 / 0 |
| License | MIT |

### Audience

- **Primary:** Prospective clients — C-suite and operations leaders evaluating the author's consulting capabilities
- **Secondary:** Other data consultants who could adopt the tool
- **Tertiary:** The author herself, for real client engagements

### Gap Analysis

The v2.0 audit identified 30 findings across architecture, UX, security, performance, and DevEx. All four improvement moves (Clean, Polish, Bridge, Grow) were executed, shipping:
- CI/CD pipeline with pip-audit
- PyPI publishing
- 5 output formats (PDF, JSON, HTML, annotated Excel, both)
- 7 analyzers (added missing-values, format-check)
- Parquet input support
- Performance improvements (regex pre-filter, --max-rows guard)

**What remains unclear for demo/client readiness:**
- Is the report output polished enough to put in front of a C-suite audience?
- Are there any embarrassing edge cases that could surface during a live demo?
- Does the GitHub repo present professionally (README, samples, docs)?
- Is the PyPI page compelling for consultants evaluating the tool?
- Are there any lingering references to "field story scorer" or v1 concepts?

### Audit Motivation

The author is about to share demo links with the first round of prospective clients. This audit is about catching anything that would:
1. Undermine credibility during a demo
2. Break during a live walkthrough
3. Look unpolished to a C-suite viewer
4. Confuse a consultant evaluating whether to adopt the tool

---

## Phase 2: Internal Review

**Lens:** What would a prospect, a fellow consultant, or a demo audience encounter that would undermine credibility?

### Tier 1 — Demo Killers (fix before sharing any links)

| # | Finding | Dimension | Why It's a Demo Killer |
|---|---------|-----------|------------------------|
| 1 | **Unhandled crash on invalid `--sheet`** — both `--sheet 1` (out of range) and `--sheet NonExistent` produce raw Python tracebacks (`IndexError`, `KeyError`) | Demo Resilience | If a prospect types the wrong sheet name during a live walkthrough, they see a Python stacktrace instead of a helpful error. Instant credibility loss. |
| 2 | **Grammar bugs in narrative output** — "1 str value **were** found" (should be "was"); "'N/A' (1 **times**)" (should be "1 time") | Report Quality | The entire value prop is "professional plain English." Grammar errors in the core deliverable directly contradict the positioning. C-suite readers notice this. |
| 3 | **Help text says ".xlsx or .csv" — doesn't mention Parquet** — `argparse` description line 30-33 is stale after Parquet was added | UX / Accuracy | A user reading `--help` won't know Parquet is supported. Minor but sloppy for a demo. |
| 4 | **`generate_sample.py` still imports numpy** — not a runtime dependency, but if someone runs the sample generator per the samples README, they'll get `ModuleNotFoundError: No module named 'numpy'` | Demo Resilience | The samples README tells users to run `python generate_sample.py`. If numpy isn't installed, it crashes. |

### Tier 2 — Professionalism Issues (fix before promoting broadly)

| # | Finding | Dimension | Impact |
|---|---------|-----------|--------|
| 5 | **`--sheet` silently ignored for CSV/Parquet** — no warning when the flag has no effect | UX | A user who passes `--sheet Revenue` on a CSV file gets results for the file with no indication their flag was meaningless. Confusing. |
| 6 | **No branding/logo on PDF title page** — the PDF is the portfolio artifact, but it has no visual identity beyond the color scheme | Report Polish | Every competitor's report output has their brand. datascope's PDF looks generic. For a consulting tool, this matters — the report should look like *your* deliverable. |
| 7 | **HTML report has no favicon or meta description** — minor but visible in browser tabs | Report Polish | Browser tab just shows "datascope diagnostic — filename" with no icon. Looks like an unfinished page. |
| 8 | **Old repo name in `docs/` brainstorm/plan files** — 25+ references to "field-story-scorer" and "scorer.py" in docs/ | Repo Presentation | Anyone browsing docs/ on GitHub sees the old project name repeatedly. These are internal dev docs, but they're public and visible. |
| 9 | **No CHANGELOG.md** — no record of what's in v2.2 vs v2.0 vs v1 | Repo Presentation | Consultants evaluating adoption want to see release cadence and what changed. PyPI page links to GitHub but there's no changelog. |
| 10 | **Repo name is still "field story scorer"** (parent directory) — the GitHub repo URL appears to be `MsShawnP/datascope` but the local directory name reveals the old name | Repo Presentation | If someone clones from GitHub this won't matter, but screenshots or file paths could leak the old name. |

### Tier 3 — Polish (nice-to-have before launch)

| # | Finding | Dimension | Impact |
|---|---------|-----------|--------|
| 11 | **No `--version` shown in stdout summary** — the report doesn't identify which datascope version produced it | Report Polish | If a consultant runs v2.2 now and v2.3 later, there's no way to tell which version produced which report. |
| 12 | **PDF footer says "datascope diagnostic" — no version or URL** | Report Polish | The footer could link to the tool or show the version for provenance. |
| 13 | **No sample HTML or annotated-Excel in `samples/output/`** — only PDF samples are committed | Repo Presentation | A GitHub visitor can't see what the HTML or Excel output looks like without installing the tool. |
| 14 | **`docs/solutions/` architecture doc references v2.0 patterns only** | Docs Staleness | Internal doc, low impact, but could confuse a contributor. |
| 15 | **No PyPI badge in README** — no quick trust signal for "this is a real published package" | Repo Presentation | Standard for any PyPI-published project. One line to add. |

### Cross-Cutting Assessment

**What's strong:**
- The tool works reliably — all 283 tests pass, all 5 output formats produce output, error handling for missing files is clean.
- Report quality (PDF, HTML) is genuinely good — professional color scheme, clear structure, severity-coded cards.
- README is excellent — clear, well-structured, shows the value prop immediately.
- JSON output is well-structured and useful.
- CLI UX is clean (aside from the --sheet crash).

**What threatens the demo:**
1. The `--sheet` crash is the only true functional bug — everything else works.
2. Grammar errors in the narrative text ("were" vs "was", "1 times" vs "1 time") undermine the "professional plain English" positioning.
3. The stale help text (no Parquet mention) and numpy dependency in generate_sample.py are paper cuts that could bite during a live demo.

**Overall readiness: 85%.** The foundation is solid. Fixing findings #1-4 (the demo killers) takes ~1-2 hours and gets this to "safe to demo." Findings #5-10 take another 2-3 hours and get it to "proud to share the repo link."

---

---

## Phase 3: Landscape Scan (Updated for v2.2)

### Market Changes Since v2.0 Audit (1 day ago, but capturing shifts)

| Event | Impact on datascope |
|-------|-------------------|
| **Fivetran acquired Great Expectations** (May 2026) | GX is being pulled into enterprise data movement. Less likely to serve the "consultant with a file" user. Widens datascope's niche. |
| **ydata-profiling rebranded to fg-data-profiling** | Organizational confusion, import path changes. Makes ydata less of a stable reference point for users choosing a tool. |
| **Pointblank (Posit) growing** — 432 stars, `pb` CLI, interactive HTML reports | Closest new competitor for "shareable output." But requires YAML/Python config for validation; no PDF; targets analysts in R/Python, not consultants. |
| **"Agentic data quality" marketing wave** | Monte Carlo, Soda, Elementary all pitching AI agents. Marketing noise, not a functional competitor to datascope's niche. |

### Updated Feature Matrix — datascope v2.2 vs Landscape

| Capability | datascope v2.2 | fg-data-profiling | Great Expectations | Pandera | Soda Core | Pointblank |
|------------|:--------------:|:-----------------:|:------------------:|:-------:|:---------:|:----------:|
| **Cell-level type detection** | **Yes** | No | No | No | No | No |
| **Excel-native reading** (no pandas coercion) | **Yes** | No | No | No | No | No |
| **Plain-English narrative** | **Yes** | No | No | No | No | Partial |
| **PDF report** | **Yes** | No | No | No | No | No |
| **HTML report** | **Yes** | Yes | No | No | No (Cloud only) | **Yes** |
| **JSON/machine-readable** | **Yes** | Yes | Yes | Yes | Yes | Yes |
| **Zero-config CLI** | **Yes** | No | No | No | Near (YAML) | Near (`pb info`) |
| **Parquet support** | **Yes** | Yes | Yes | Yes | Yes | Yes |
| **PyPI published** | **Yes** | Yes | Yes | Yes | Yes | Yes |
| **CI/CD pipeline** | **Yes** | Yes | Yes | Yes | Yes | Yes |
| **CSV support** | Yes | Yes | Yes | Yes | Yes | Yes |
| **Annotated source output** | **Yes** | No | No | No | No | No |
| **Custom validation rules** | No | No | **Yes** | **Yes** | **Yes** | **Yes** |
| **Statistical profiling** | No | **Yes** | No | No | No | Partial |
| **Database support** | No | No | Yes | No | **Yes** | **Yes** |
| **Polars support** | No | No | No | **Yes** | No | **Yes** |
| **Large file performance** | Weak (>100K) | Weak | Good | Good | Good | Good |
| **Community/stars** | New (0) | 13.6k | 11.5k | 4.3k | 2.3k | 432 |

### What Changed Since v2.0 Audit

**Gaps closed by v2.2:**
- ~~No machine-readable output~~ → JSON output shipped
- ~~No HTML report~~ → HTML shipped
- ~~No Parquet support~~ → Parquet shipped
- ~~No CI/CD~~ → GitHub Actions (test + lint + audit + publish)
- ~~No PyPI~~ → Published as `datascope-dq`
- ~~Single output format~~ → 5 formats
- ~~5 analyzers~~ → 7 analyzers (added missing-values, format-check)

**Gaps that remain (intentionally):**
- No custom validation rules (GX/Pandera territory — don't compete)
- No database support (Soda territory — stay in file lane)
- No statistical profiling (fg-data-profiling territory — datascope finds *problems*, not *stats*)
- No Polars support (low priority for target audience)
- No drift detection (whylogs territory — datascope is point-in-time)

### datascope's Updated Competitive Position

**Still unique (no competitor does this):**
1. Cell-level type detection via openpyxl (technical moat — unchanged)
2. "Assumption vs. reality" narrative framing for non-technical readers
3. PDF as first-class output format (still zero competitors with native PDF)
4. Annotated Excel output highlighting problem cells in the source file
5. True zero-config: `datascope file.xlsx` → full report, no setup

**Stronger since v2.0:**
6. JSON + HTML output bridges the engineer audience (was the #1 gap)
7. PyPI publishing + CI/CD provides trust signals
8. Parquet support covers the modern data stack input format

**Still weaker:**
9. No community — 0 external users/stars (biggest risk for consultant adoption)
10. Performance ceiling at ~100K rows (fine for target audience)
11. No web UI or SaaS (fine for now — CLI + report is the right form factor)

### The Niche Assessment (Revised)

The v2.0 audit concluded: *"The market is leaving the 'consultant analyzes a client's messy Excel file and needs a professional report' use case completely unaddressed."*

**This is still true.** In fact it's MORE true:
- GX being absorbed by Fivetran makes it more enterprise/pipeline focused, not less
- fg-data-profiling's organizational turmoil (rename, maintainer change) creates uncertainty
- Pointblank is the closest emerging competitor for "shareable output" but still requires configuration and doesn't produce PDF
- The "agentic" wave is all about pipelines and monitoring, not one-shot file audits

**datascope v2.2 now covers the full minimum-viable competitive surface:**
- Multiple input formats (Excel, CSV, Parquet)
- Multiple output formats (PDF, HTML, JSON, annotated Excel)
- Published and installable (`pip install datascope-dq`)
- CI/CD trust signals
- Professional report quality

**What would make it a clear winner for the consulting niche:**
- Social proof (stars, testimonials, case studies)
- Branding on the PDF report
- A demo page or hosted example report
- Logo/visual identity

---

---

## Phase 4: Synthesis & Next Moves

### Strategic Frame

datascope v2.2 is **functionally complete** for its niche. The tool works, the reports are professional, the feature set covers input/output formats that matter. The gap is no longer "can it do X?" — it's "does it *present* as a credible professional tool when a prospect evaluates it?"

This is a positioning and polish problem, not a feature problem.

### Priority Matrix

Cross-referencing Phase 2 findings with Phase 3 landscape position:

```
                        HIGH landscape impact
                              │
           ┌──────────────────┼──────────────────┐
           │   BRAND          │   DEMO-PROOF      │
           │   (Move 2)       │   (Move 1)        │
           │   PDF branding   │   Fix crashes      │
           │   Hosted demo    │   Fix grammar      │
           │   Logo/identity  │   Fix help text    │
LOW effort ├──────────────────┼──────────────────┤ HIGH effort
           │   HYGIENE        │   GROWTH           │
           │   (Move 3)       │   (Move 4)         │
           │   Changelog      │   Landing page     │
           │   PyPI badge     │   Community         │
           │   Sample outputs │   Case studies     │
           │                  │                    │
           └──────────────────┼──────────────────┘
                              │
                        LOW landscape impact
```

---

### Move 1: DEMO-PROOF — Nothing breaks live (~1-2 hours)

*Goal: A prospect can run `datascope` on any file during a call without seeing a crash or grammar error.*

| Task | Phase 2 Finding | Effort |
|------|----------------|--------|
| Catch invalid `--sheet` (index out of range + name not found) → friendly error message | #1 | 20 min |
| Fix grammar: "1 str value were" → "was"; "(1 times)" → "(1 time)" �� audit all templates for singular/plural | #2 | 30 min |
| Update argparse description to mention `.parquet` alongside `.xlsx` and `.csv` | #3 | 5 min |
| Replace `numpy` in `generate_sample.py` with stdlib `random` (or add numpy to `[dev]` extras) | #4 | 20 min |
| Warn when `--sheet` is passed for CSV/Parquet files | #5 | 10 min |

**Why this is Move 1:** These are the only things that can *embarrass you live*. Everything else is about how good it looks when no one's watching. This is about when someone IS watching.

---

### Move 2: BRAND — The report IS the product (~2-3 hours)

*Goal: A PDF or HTML report from datascope looks like it came from a professional consulting tool, not a side project.*

| Task | Phase 2 Finding | Landscape Rationale | Effort |
|------|----------------|--------------------:|--------|
| Add configurable branding to PDF title page (tool name + optional logo placeholder) | #6 | No competitor has PDF — make datascope's PDF look like a *product* | 45 min |
| Add datascope version + URL to PDF footer | #12 | Provenance — which version produced this report | 15 min |
| Add favicon + meta tags to HTML report | #7 | Pointblank has polished HTML; datascope's should match | 15 min |
| Add `datascope --version` to report metadata (JSON `"generator"` field) | #11 | Machine-readable provenance | 10 min |
| Create a hosted example report (HTML) — link from README | Landscape #9 (social proof) | Prospects can see the output quality without installing | 45 min |

**Why this is Move 2:** The report is what prospects see. It's the artifact they judge you by. Right now it's functional but anonymous — it doesn't *own* its identity. Adding branding turns "a PDF someone generated" into "a datascope diagnostic."

---

### Move 3: REPO HYGIENE — The GitHub page passes scrutiny (~1 hour)

*Goal: A consultant browsing the GitHub repo sees a maintained, professional project.*

| Task | Phase 2 Finding | Effort |
|------|----------------|--------|
| Add PyPI badge + CI badge to README top | #15 | 5 min |
| Create CHANGELOG.md (v1.0 → v2.0 → v2.1 → v2.2 with highlights) | #9 | 30 min |
| Commit sample HTML + annotated-Excel outputs to `samples/output/` | #13 | 10 min |
| Remove or archive `docs/plans/` and `docs/brainstorms/` (internal dev docs with old names) | #8 | 15 min |

**Why this is Move 3:** These are trust signals. A consultant evaluating whether to use or recommend datascope will check the repo. Badges, changelog, and sample outputs answer "is this maintained?" and "what does the output look like?" without requiring installation.

---

### Move 4: GROWTH — Social proof and discovery (ongoing)

*Goal: People find datascope and see that others use it.*

| Task | Landscape Rationale | Effort |
|------|--------------------:|--------|
| Create a simple landing page or GitHub Pages site with example reports | Only tool in niche with PDF + HTML — show it | 3-4 hr |
| Write a "how I built this" or "data quality for consultants" blog post | SEO + positioning for the unoccupied niche | 2-3 hr |
| Submit to Python data quality lists/awesome-lists | Discovery in the ecosystem | 30 min |
| Add a "Used by" or testimonial section after first client engagement | Social proof — the strongest trust signal | Ongoing |
| Consider a short demo video (2 min: file in → report out) | Shows zero-config UX without installation | 1-2 hr |

**Why this is Move 4:** The tool is ready. The gap is now awareness. No amount of code improvement matters if prospects can't find it or don't see social proof. But this depends on Moves 1-3 being done first — don't promote something that can crash during a demo.

---

### What NOT to Build

| Temptation | Why to Resist |
|-----------|---------------|
| Custom validation rules | GX + Pandera own this. You'd compete with 15k-star projects on their turf. |
| Database connectivity | Soda owns this. Stay in the file lane — it's where consultants live. |
| Statistical profiling | fg-data-profiling owns this. datascope finds *problems*, not *distributions*. |
| Web UI / SaaS | Premature. The CLI + report is the right form factor for demos and consulting. |
| Polars backend | Your audience uses Excel and CSV. Polars is an engineer concern. |
| AI-generated fix suggestions | Marketing noise in the landscape. Concrete fix recommendations > vague AI. |

---

### Execution Order

```
Week 1 (before sharing links):
  Move 1: DEMO-PROOF     [~1-2 hours]
  Move 2: BRAND           [~2-3 hours]

Week 2 (before promoting repo):
  Move 3: REPO HYGIENE    [~1 hour]

Ongoing (after first client conversations):
  Move 4: GROWTH          [as time allows]
```

---

### The One-Sentence Thesis

**datascope is the only zero-config tool that produces professional PDF/HTML reports from messy data files — fix the 4 demo-killers, brand the report output, and it's ready for prospects.**
