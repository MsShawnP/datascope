"""Integration tests -- full pipeline from sample files through PDF output.

These tests exercise the complete datascope pipeline: load -> analyse ->
process findings -> write PDF, verifying that the components work together
end-to-end.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from datascope.analyzers import (
    analyze_cardinality,
    analyze_leading_zeros,
    analyze_mixed_dates,
    analyze_sentinels,
    analyze_type_consistency,
)
from datascope.findings import process_findings
from datascope.loaders import load, load_excel
from datascope.models import Finding, LoaderResult, Severity
from datascope.reports import write_pdf

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples" / "input"
SAMPLE_XLSX = SAMPLES_DIR / "sample_mixed_types.xlsx"
SAMPLE_SALES = SAMPLES_DIR / "sample_sales.xlsx"


def _run_full_pipeline(
    path: Path,
    output_dir: Path,
    sheet: str | int = 0,
) -> tuple[list[Finding], Path]:
    """Run the complete pipeline and return (findings, pdf_path)."""
    if path.suffix.lower() == ".xlsx":
        result = load_excel(path, sheet=sheet)
    else:
        result = load(path)

    all_findings: list[Finding] = []
    all_findings.extend(analyze_type_consistency(result))
    all_findings.extend(analyze_sentinels(result))
    all_findings.extend(analyze_leading_zeros(result))
    all_findings.extend(analyze_mixed_dates(result))
    all_findings.extend(analyze_cardinality(result))

    processed = process_findings(all_findings)

    output_name = f"{path.stem}_diagnostic.pdf"
    output_path = output_dir / output_name
    write_pdf(processed, result.source_metadata, output_path)

    return processed, output_path


def _write_csv(tmp_path: Path, text: str, name: str = "test.csv") -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")
    return p


# ===================================================================
# sample_mixed_types.xlsx -- the primary test fixture
# ===================================================================

class TestMixedTypesSample:

    def test_sample_file_exists(self):
        assert SAMPLE_XLSX.exists(), f"Missing sample file: {SAMPLE_XLSX}"

    def test_full_pipeline_produces_pdf(self, tmp_path):
        findings, pdf_path = _run_full_pipeline(SAMPLE_XLSX, tmp_path)
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_findings_are_not_empty(self, tmp_path):
        findings, _ = _run_full_pipeline(SAMPLE_XLSX, tmp_path)
        assert len(findings) > 0, "Expected findings from the mixed-types sample"

    def test_all_findings_have_severity(self, tmp_path):
        findings, _ = _run_full_pipeline(SAMPLE_XLSX, tmp_path)
        for f in findings:
            assert f.severity is not None, (
                f"Finding for {f.field_name} missing severity"
            )

    def test_all_findings_have_narrative_text(self, tmp_path):
        findings, _ = _run_full_pipeline(SAMPLE_XLSX, tmp_path)
        for f in findings:
            assert f.assumption is not None, (
                f"Finding for {f.field_name} missing assumption"
            )
            assert f.reality is not None, (
                f"Finding for {f.field_name} missing reality"
            )

    def test_findings_sorted_by_severity_descending(self, tmp_path):
        findings, _ = _run_full_pipeline(SAMPLE_XLSX, tmp_path)
        if len(findings) >= 2:
            for i in range(len(findings) - 1):
                a, b = findings[i], findings[i + 1]
                assert a.severity.value >= b.severity.value, (
                    f"Findings not sorted: {a.field_name} ({a.severity}) "
                    f"before {b.field_name} ({b.severity})"
                )

    def test_pdf_filename_matches_convention(self, tmp_path):
        _, pdf_path = _run_full_pipeline(SAMPLE_XLSX, tmp_path)
        assert pdf_path.name == "sample_mixed_types_diagnostic.pdf"


# ===================================================================
# sample_sales.xlsx -- second sample
# ===================================================================

class TestSalesSample:

    def test_sample_file_exists(self):
        assert SAMPLE_SALES.exists(), f"Missing sample file: {SAMPLE_SALES}"

    def test_full_pipeline_produces_pdf(self, tmp_path):
        findings, pdf_path = _run_full_pipeline(SAMPLE_SALES, tmp_path)
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0


# ===================================================================
# CSV through the full pipeline
# ===================================================================

class TestCsvPipeline:

    def test_clean_csv_produces_pdf(self, tmp_path):
        csv_path = _write_csv(tmp_path, """\
            id,name,value
            1,Alice,100
            2,Bob,200
            3,Carol,300
        """)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        findings, pdf_path = _run_full_pipeline(csv_path, out_dir)
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_mixed_csv_detects_issues(self, tmp_path):
        csv_path = _write_csv(tmp_path, """\
            product,price,code
            Widget,9.99,001
            Gadget,N/A,002
            Doohickey,14.50,003
            Thingamajig,12.00,N/A
        """)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        findings, pdf_path = _run_full_pipeline(csv_path, out_dir)
        assert pdf_path.exists()
        # Should detect at least one issue (sentinel or mixed types)
        assert len(findings) > 0  # data has sentinels and mixed types

    def test_empty_csv_pipeline_no_crash(self, tmp_path):
        csv_path = _write_csv(tmp_path, """\
            a,b,c
        """)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        findings, pdf_path = _run_full_pipeline(csv_path, out_dir)
        assert pdf_path.exists()
        assert len(findings) == 0


# ===================================================================
# Pipeline component contracts
# ===================================================================

class TestPipelineContracts:

    def test_loader_returns_loader_result(self):
        result = load(SAMPLE_XLSX)
        assert isinstance(result, LoaderResult)

    def test_analyzers_return_finding_lists(self):
        result = load(SAMPLE_XLSX)
        for analyzer_fn in [
            analyze_type_consistency,
            analyze_sentinels,
            analyze_leading_zeros,
            analyze_mixed_dates,
            analyze_cardinality,
        ]:
            findings = analyzer_fn(result)
            assert isinstance(findings, list)
            for f in findings:
                assert isinstance(f, Finding)

    def test_process_findings_enriches_all_fields(self):
        result = load(SAMPLE_XLSX)
        all_findings: list[Finding] = []
        all_findings.extend(analyze_type_consistency(result))
        all_findings.extend(analyze_sentinels(result))

        if all_findings:
            processed = process_findings(all_findings)
            for f in processed:
                assert f.severity is not None
                assert isinstance(f.severity, Severity)

    def test_write_pdf_returns_path(self, tmp_path):
        result = load(SAMPLE_XLSX)
        all_findings = analyze_type_consistency(result)
        processed = process_findings(all_findings)

        pdf_path = tmp_path / "test_output.pdf"
        returned = write_pdf(processed, result.source_metadata, pdf_path)
        assert isinstance(returned, Path)
        assert returned.exists()
