---
date: 2026-05-14
topic: data-quality-diagnostic-v2
---

# Data Quality Diagnostic Tool — v2 Product Transformation

## Summary

A data quality diagnostic tool that deeply analyzes datasets, surfaces hidden problems in plain English with severity ratings, explains downstream business impact, recommends fixes, and provides prevention standards. Positioned as a professional deliverable for data consultants, client dev teams, and developers tackling unfamiliar data. Replaces the current field-story-scorer v1.0 scoring approach with actionable, audience-appropriate findings.

---

## Problem Frame

Data created upstream — by manufacturing teams entering UPCs, inventory staff assigning product codes, offshore developers choosing column types — silently breaks systems downstream. A product code with letters where EDI expects numbers. An Oracle number type that Crystal Reports can't read. Fifteen "N/A" strings buried in 500 numeric rows that pandas silently drops, skewing every calculation by 3%.

These problems share three properties: they're invisible on the surface, they're created by people who don't understand the downstream consequences, and they're discovered too late — when a deliverable is blocked or a report produces obviously wrong numbers.

The bottleneck isn't detection. An experienced data professional can find these problems. The bottleneck is **articulation** — translating what's wrong into language that non-technical people can understand and act on. The upstream person who created the problem doesn't understand data types, doesn't work with the downstream systems, and doesn't see the consequences. A tool that makes the problem undeniable — showing exactly what's broken and what it costs — closes the articulation gap that keeps these issues from getting fixed.

This problem is growing. Frontend developers increasingly take on data-intensive work without data quality expertise. They don't know what "bad data" looks like, don't know to check for it, and accept surface-level answers from AI tools without pushing deeper.

Existing tools either score data in abstract dimensions (the current v1.0 approach) or require the user to know what questions to ask. Casual AI prompting gives surface-level answers — most users accept the first response without pushing back. What's missing is a tool that embodies expert-level data interrogation and translates findings into language that non-technical readers can understand and act on.

---

## Actors

- A1. **Data Consultant**: Runs the tool against client datasets and delivers the resulting report as a professional service. Has data expertise; needs the tool to amplify that expertise into a client-ready deliverable.
- A2. **Client Data Person / Developer**: Receives the report. May be a DBA, a frontend developer handling data work, or a business analyst. Needs to understand what's wrong, why it matters to their systems, and what to fix — without needing data expertise themselves.
- A3. **Upstream Data Creator**: The person who created the problematic data (manufacturing, inventory, ordering staff). May never see the report directly, but is the root cause. The report must make the case clearly enough that A2 can relay it upstream.

---

## Key Flows

- F1. **Client Data Assessment**
  - **Trigger:** Consultant receives a dataset from a client engagement
  - **Actors:** A1
  - **Steps:** Point tool at dataset → tool analyzes and generates findings → tool produces professional report → consultant reviews and delivers to client
  - **Outcome:** Client has a comprehensive, plain-English data quality assessment with prioritized findings and fix recommendations
  - **Covered by:** R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13

- F2. **Developer Self-Service**
  - **Trigger:** Developer receives an unfamiliar dataset they need to work with
  - **Actors:** A2
  - **Steps:** Run tool against dataset → read findings → understand what's wrong and why → fix issues based on recommendations
  - **Outcome:** Developer understands hidden data problems and has actionable fix steps, without needing external data expertise
  - **Covered by:** R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12

- F3. **Data Quality Case-Building**
  - **Trigger:** Consultant discovers data issues that need stakeholder buy-in to fix
  - **Actors:** A1, indirectly A3
  - **Steps:** Run tool against problematic dataset → generate evidence report → present findings to stakeholders → stakeholders understand business impact and authorize fixes
  - **Outcome:** Non-technical stakeholders understand why data quality matters and approve remediation work
  - **Covered by:** R7, R8, R9, R12, R13

---

## Requirements

**Analysis engine**

- R1. Analyze datasets from multiple sources: Excel (.xlsx) and CSV are required for v2. Database support (starting with one engine — e.g., SQLite or PostgreSQL) is a stretch goal; additional engines are deferred
- R2. Perform cell-level type analysis by default — detect what tools like pandas silently coerce, without requiring a special flag
- R3. Detect hidden sentinel values: strings like "N/A", "TBD", "—", "pending" buried in otherwise-numeric or otherwise-typed columns
- R4. Detect type inconsistencies within columns: mixed types that surface tools would mask (e.g., 485 numbers + 15 strings reported as float64)
- R5. Detect format inconsistencies: mixed date formats, inconsistent code patterns, leading-zero mismatches
- R6. Detect cardinality and uniqueness anomalies: duplicate IDs, near-constant columns, columns with suspiciously low or high uniqueness
- R7. Classify the severity of each finding based on likely downstream impact:
    - **Critical**: data corruption, silent calculation errors, system rejection (e.g., mixed types in a numeric column that skew aggregations)
    - **Warning**: potential misinterpretation or fragile behavior that hasn't broken yet (e.g., inconsistent formatting that may cause downstream key mismatches)
    - **Info**: style, convention, or low-risk anomalies worth noting (e.g., near-constant columns, unusual cardinality)

**Finding presentation**

- R8. Express each finding as an "assumption vs. reality" statement: what the data appears to be vs. what it actually contains
- R9. Explain the downstream business impact of each finding in plain English — what breaks, what gets skewed, what gets rejected
- R10. Provide a specific fix recommendation for each finding
- R11. Provide a plain-English prevention rule for each finding: "what right looks like going forward" — a human-readable standard the client's team can implement in whatever system they use
- R12. Order and group findings by severity so readers know what to fix first

**Report output**

- R13. Generate a professional report suitable for client delivery
- R14. Design the report for non-technical readers: no jargon, no composite scores as the primary organizing concept, no unexplained statistical metrics
- R15. Include an executive summary: overall data health assessment and the top-priority findings at a glance

**Product identity**

- R16. Choose a new product name that communicates: data quality diagnosis, plain-English accessibility, and professional credibility
- R17. Portfolio-grade code quality, documentation, and presentation — suitable for featuring on LinkedIn and a personal website as a demonstration of domain expertise and engineering craft

---

## Acceptance Examples

- AE1. **Covers R2, R4, R8, R9, R11.** Given a CSV with a `revenue` column containing 485 numeric values and 15 text values ("N/A", "pending"), the tool reports something like: "Column `revenue` appears numeric, but 15 of 500 values are text strings. Any sum or average calculated on this column will silently exclude these rows, potentially understating totals. Severity: Critical. Prevention: Revenue values should be strictly numeric with no text entries; use a dedicated status column for flags like 'N/A' or 'pending'."

- AE2. **Covers R5, R8, R11.** Given an Excel file with a `product_code` column where 230 values have leading zeros and 270 do not, the tool reports something like: "Column `product_code` has inconsistent formatting — some values have leading zeros, some don't. Systems that treat these as numbers will strip leading zeros, creating duplicate or invalid codes. Prevention: Product codes should be stored as text with consistent fixed-width formatting."

- AE3. **Covers R1.** Given a database connection string and table name, the tool connects, analyzes the table, and produces the same quality of findings as for an Excel or CSV file.

- AE4. **Covers R7, R12, R15.** Given a dataset with 3 critical findings, 5 warnings, and 2 informational notes, the executive summary highlights the 3 critical findings first, and the full report groups all findings by severity tier.

---

## Success Criteria

- A data consultant can run the tool against a client's dataset and deliver the resulting report as a professional service — findings are factually complete and clearly written enough that the consultant adds context, not corrections
- A frontend developer with no data expertise can read the report and understand what needs fixing, why, and how — without asking someone to explain
- The report makes data quality problems undeniable — the "assumption vs. reality" framing shows exactly what's broken and what it costs, closing the articulation gap between data experts and non-technical stakeholders
- The tool detects problems that surface-level analysis misses — validated by cell-level type detection that catches what pandas, SQL drivers, and similar tools silently coerce
- The codebase, documentation, and output quality are portfolio-grade: someone viewing this on LinkedIn or a personal website would conclude the author understands data quality, builds real tools, and ships production-grade software

---

## Scope Boundaries

### Deferred for later

- **v3: Executable validation code generation** — SQL constraints, spreadsheet validation formulas, schema definitions. Explicitly planned as the next major evolution after v2 ships.
- Web UI or SaaS form factor
- Real-time or ongoing data quality monitoring
- Interactive / conversational mode (follow-up questions about findings)

### Outside this product's identity

- General-purpose exploratory data analysis (EDA) — this tool diagnoses data quality, not data insights
- Data cleaning or transformation — this diagnoses and recommends, it does not modify data
- ETL pipeline or data integration tooling
- Database administration or schema migration

---

## Key Decisions

- **Combined three product approaches into one**: diagnostic report (consulting deliverable) + reality translator (assumption vs. reality framing) + prevention kit (plain-English validation rules). Each reinforces the others.
- **Strict-types analysis is always on**: Detecting what surface-level tools (pandas, SQL drivers, Excel viewers) silently coerce is the core engine, not an optional flag. This is the technical moat — but the detection strategy differs by format: openpyxl cell-level types for Excel, heuristic raw-string inference for CSV, declared-vs-actual type comparison for databases.
- **Composite scores removed**: v1's 0-1 dimensional scores are replaced by specific, actionable findings ordered by severity (R7, R12). Severity-based ordering is the organizing mechanism, not composite scoring.
- **"Assumption vs. reality" is the primary framing**: Each finding shows the gap between what the data appears to be and what it actually is. This framing is educational and non-confrontational — it shows reality rather than declaring judgment.
- **Plain-English validation rules in v2, executable code in v3**: Prevention standards are human-readable in v2. Generating actual SQL/formula output is a v3 goal.
- **CLI as primary interface for v2**: The tool runs from the command line. The report output is the deliverable, not the CLI itself.

---

## Dependencies / Assumptions

- Python remains the implementation language
- The detection engine uses format-specific strategies unified by a common diagnostic goal: Excel uses openpyxl cell-level types (existing), CSV and database support require new detection approaches (see Outstanding Questions)
- v1 already implements: load_strict() for Excel cell-level type reading, type_consistency scoring, PDF and Excel report generation. v2 builds on this foundation rather than starting from scratch
- Database support requires connection string handling and appropriate drivers (scope of which databases TBD in planning)
- reportlab and/or openpyxl remain viable for report generation, or alternatives are evaluated during planning

---

## Outstanding Questions

### Deferred to Planning

- [Needs research] Which database engines to support in v2 — PostgreSQL, MySQL, SQLite, SQL Server, Oracle? Start with one or two, or all?
- [Needs research] Report format — PDF, Excel, HTML, or multiple? What best serves the "hand to a client" use case?
- [Technical] Codebase structure — keep single-file design or modularize for maintainability and v3 extensibility?
- [Technical] How to structure the analysis engine for extensibility toward v3 validation code generation
- [Needs research] New product name — explore options during planning that communicate data quality diagnosis, accessibility, and professional credibility
- [Technical] Severity classification model — what criteria map findings to critical / warning / info?
- [Technical] CSV detection strategy — with no cell-level type metadata, what heuristic approach detects mixed types, sentinel values, and coercion risks from raw strings?
- [Technical] Database detection strategy — how to compare declared column types against actual value patterns to surface type mismatches (e.g., the Oracle number-type problem)?
- [Product] Do A1 (consultant), A2 (developer), and A3 (upstream creator) need different output formats, or does one report serve all three audiences? If different, how to avoid building three products?
- [Technical] NL generation approach — how to produce publication-quality English findings: templates, LLM-assisted generation, rule-based composition, or hybrid? v1 is deterministic scoring; v2 promises readable prose
- [Technical] Sentinel detection (R3) is entirely new code with no v1 foundation. Strategy needed: configurable list-based approach, heuristic detection, or hybrid? How to distinguish "N/A" the sentinel from "N/A" as a legitimate category value?
- [Scope] R5 bundles three distinct detection problems (mixed date formats, inconsistent code patterns, leading-zero mismatches) with no existing code foundation. Should R5 be split into sub-requirements, and which subset is v2-essential?
- [Technical] Report format (R13-R15) must be selected before implementation — PDF, Excel, HTML, and Markdown are structurally different deliverables with different libraries and layout constraints
