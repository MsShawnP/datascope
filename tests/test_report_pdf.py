"""Tests for datascope.reports.pdf -- PDF report generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from datascope.findings.pipeline import process_findings
from datascope.findings.severity import classify_severity
from datascope.findings.composer import compose_finding
from datascope.models import Finding, FindingType, Severity
from datascope.reports.pdf import write_pdf


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULT_METADATA = {
    "filename": "test_data.csv",
    "row_count": 1000,
    "column_count": 12,
}


def _make_finding(
    finding_type: FindingType,
    evidence: dict,
    field_name: str = "test_col",
) -> Finding:
    """Build a fully-populated Finding (classified + composed)."""
    f = Finding(field_name=field_name, finding_type=finding_type, evidence=evidence)
    f.severity = classify_severity(f)
    compose_finding(f)
    return f


def _critical_finding(field_name: str = "revenue") -> Finding:
    return _make_finding(
        FindingType.TYPE_INCONSISTENCY,
        {
            "majority_type": "numeric",
            "majority_count": 485,
            "minority_types": [
                {"type_name": "str", "count": 15, "examples": ["N/A", "pending", "TBD"]},
            ],
            "total_non_null": 500,
            "majority_pct": 97.0,
        },
        field_name=field_name,
    )


def _warning_finding(field_name: str = "zip_code") -> Finding:
    return _make_finding(
        FindingType.LEADING_ZEROS,
        {
            "leading_zero_count": 10,
            "no_leading_zero_count": 40,
            "examples_with_zeros": ["00123", "00456", "00789"],
            "examples_without_zeros": ["123", "456"],
            "total_checked": 50,
        },
        field_name=field_name,
    )


def _info_finding(field_name: str = "status") -> Finding:
    return _make_finding(
        FindingType.NEAR_CONSTANT,
        {
            "unique_count": 2,
            "total_count": 5000,
            "uniqueness_ratio": 0.0004,
            "top_values": [
                {"value": "Active", "count": 4990},
                {"value": "Inactive", "count": 10},
            ],
        },
        field_name=field_name,
    )


# ---------------------------------------------------------------------------
# Scenario 1: Happy path -- 3 critical + 2 warning + 1 info
# ---------------------------------------------------------------------------

class TestHappyPathMixedFindings:
    """PDF generated with a realistic mix of findings."""

    @pytest.fixture()
    def pdf_path(self, tmp_path: Path) -> Path:
        findings = [
            _critical_finding("revenue"),
            _critical_finding("cost"),
            _critical_finding("margin"),
            _warning_finding("zip_code"),
            _warning_finding("product_code"),
            _info_finding("status"),
        ]
        findings = process_findings(findings)
        return write_pdf(findings, _DEFAULT_METADATA, tmp_path / "report.pdf")

    def test_file_created(self, pdf_path: Path):
        assert pdf_path.exists()

    def test_file_non_zero_size(self, pdf_path: Path):
        assert pdf_path.stat().st_size > 0

    def test_returns_path_object(self, pdf_path: Path):
        assert isinstance(pdf_path, Path)

    def test_file_starts_with_pdf_magic(self, pdf_path: Path):
        header = pdf_path.read_bytes()[:5]
        assert header == b"%PDF-"


# ---------------------------------------------------------------------------
# Scenario 2: Executive summary builds without error
# ---------------------------------------------------------------------------

class TestExecutiveSummary:
    """Verify the PDF builds successfully (proves executive summary renders)."""

    def test_builds_with_critical_findings(self, tmp_path: Path):
        findings = process_findings([
            _critical_finding("amount"),
            _warning_finding("code"),
        ])
        result = write_pdf(findings, _DEFAULT_METADATA, tmp_path / "exec.pdf")
        assert result.exists()
        assert result.stat().st_size > 0

    def test_builds_with_no_critical(self, tmp_path: Path):
        findings = process_findings([
            _warning_finding("zip"),
            _info_finding("country"),
        ])
        result = write_pdf(findings, _DEFAULT_METADATA, tmp_path / "no_crit.pdf")
        assert result.exists()


# ---------------------------------------------------------------------------
# Scenario 3: Long text content renders without error
# ---------------------------------------------------------------------------

class TestLongTextContent:
    """Findings with verbose text should not cause layout overflow."""

    def test_long_narrative_fields(self, tmp_path: Path):
        f = _critical_finding("revenue")
        # Overwrite with extra-long text.
        f.assumption = "This is a very long assumption. " * 30
        f.reality = "This is a very long reality description. " * 30
        f.impact = "This is a very long impact statement. " * 30
        f.fix_recommendation = "This is a very long fix recommendation. " * 30
        f.prevention_rule = "This is a very long prevention rule. " * 30

        result = write_pdf([f], _DEFAULT_METADATA, tmp_path / "long.pdf")
        assert result.exists()
        assert result.stat().st_size > 0


# ---------------------------------------------------------------------------
# Scenario 4: Zero findings
# ---------------------------------------------------------------------------

class TestZeroFindings:
    """Report still generates with a 'no issues found' message."""

    @pytest.fixture()
    def pdf_path(self, tmp_path: Path) -> Path:
        return write_pdf([], _DEFAULT_METADATA, tmp_path / "empty.pdf")

    def test_file_created(self, pdf_path: Path):
        assert pdf_path.exists()

    def test_file_non_zero_size(self, pdf_path: Path):
        assert pdf_path.stat().st_size > 0

    def test_valid_pdf_header(self, pdf_path: Path):
        header = pdf_path.read_bytes()[:5]
        assert header == b"%PDF-"


# ---------------------------------------------------------------------------
# Scenario 5: Single finding
# ---------------------------------------------------------------------------

class TestSingleFinding:
    """Report structure still makes sense with just one finding."""

    def test_single_critical(self, tmp_path: Path):
        findings = process_findings([_critical_finding("revenue")])
        result = write_pdf(findings, _DEFAULT_METADATA, tmp_path / "single.pdf")
        assert result.exists()
        assert result.stat().st_size > 0

    def test_single_info(self, tmp_path: Path):
        findings = process_findings([_info_finding("status")])
        result = write_pdf(findings, _DEFAULT_METADATA, tmp_path / "single_info.pdf")
        assert result.exists()
        assert result.stat().st_size > 0


# ---------------------------------------------------------------------------
# Scenario 6: Very long field names and evidence text
# ---------------------------------------------------------------------------

class TestLongFieldNames:
    """Long field names should not blow up the layout."""

    def test_500_char_field_name(self, tmp_path: Path):
        long_name = "x" * 500
        f = _critical_finding(long_name)
        result = write_pdf([f], _DEFAULT_METADATA, tmp_path / "longname.pdf")
        assert result.exists()
        assert result.stat().st_size > 0

    def test_field_name_with_special_chars(self, tmp_path: Path):
        special_name = "amount <USD> & tax (%) [2024]"
        f = _critical_finding(special_name)
        result = write_pdf([f], _DEFAULT_METADATA, tmp_path / "special.pdf")
        assert result.exists()
        assert result.stat().st_size > 0


# ---------------------------------------------------------------------------
# Scenario 7: Output directory doesn't exist -- created automatically
# ---------------------------------------------------------------------------

class TestAutoCreateDirectory:
    """write_pdf should create parent directories that don't exist."""

    def test_nested_dir_created(self, tmp_path: Path):
        deep_path = tmp_path / "a" / "b" / "c" / "report.pdf"
        result = write_pdf([], _DEFAULT_METADATA, deep_path)
        assert result.exists()
        assert result.parent.is_dir()

    def test_returns_resolved_path(self, tmp_path: Path):
        nested = tmp_path / "sub" / "out.pdf"
        result = write_pdf([], _DEFAULT_METADATA, nested)
        assert result == nested


# ---------------------------------------------------------------------------
# Scenario 8: Integration -- build findings from scratch, process, render
# ---------------------------------------------------------------------------

class TestIntegrationPipeline:
    """Full pipeline: raw findings -> process_findings -> write_pdf."""

    def test_full_pipeline(self, tmp_path: Path):
        raw_findings = [
            Finding(
                field_name="revenue",
                finding_type=FindingType.TYPE_INCONSISTENCY,
                evidence={
                    "majority_type": "numeric",
                    "majority_count": 90,
                    "minority_types": [
                        {"type_name": "str", "count": 10, "examples": ["N/A", "??"]},
                    ],
                    "total_non_null": 100,
                    "majority_pct": 90.0,
                },
            ),
            Finding(
                field_name="cost",
                finding_type=FindingType.SENTINEL_VALUE,
                evidence={
                    "sentinels_found": [
                        {"value": "N/A", "count": 3, "normalized": "n/a"},
                    ],
                    "column_majority_type": "numeric",
                    "total_non_null": 100,
                    "sentinel_pct": 3.0,
                },
            ),
            Finding(
                field_name="zip_code",
                finding_type=FindingType.LEADING_ZEROS,
                evidence={
                    "leading_zero_count": 5,
                    "no_leading_zero_count": 45,
                    "examples_with_zeros": ["00123"],
                    "examples_without_zeros": ["456"],
                    "total_checked": 50,
                },
            ),
            Finding(
                field_name="invoice_date",
                finding_type=FindingType.MIXED_DATES,
                evidence={
                    "formats_found": ["%Y-%m-%d", "%m/%d/%Y"],
                    "examples_per_format": {
                        "%Y-%m-%d": ["2026-01-15"],
                        "%m/%d/%Y": ["01/15/2026"],
                    },
                    "total_date_values": 200,
                },
            ),
            Finding(
                field_name="country",
                finding_type=FindingType.NEAR_CONSTANT,
                evidence={
                    "unique_count": 1,
                    "total_count": 500,
                    "uniqueness_ratio": 0.002,
                    "top_values": [{"value": "US", "count": 500}],
                },
            ),
            Finding(
                field_name="order_id",
                finding_type=FindingType.DUPLICATE_IDS,
                evidence={
                    "unique_count": 980,
                    "total_count": 1000,
                    "uniqueness_ratio": 0.98,
                    "duplicate_values": ["ID-001", "ID-002"],
                },
            ),
        ]

        processed = process_findings(raw_findings)
        assert len(processed) == 6

        metadata = {
            "filename": "sales_data.xlsx",
            "row_count": 1000,
            "column_count": 6,
        }
        result = write_pdf(processed, metadata, tmp_path / "integration.pdf")

        assert result.exists()
        assert result.stat().st_size > 1000  # Non-trivial content
        assert result.read_bytes()[:5] == b"%PDF-"


# ---------------------------------------------------------------------------
# Package exports
# ---------------------------------------------------------------------------

class TestPackageExports:
    """datascope.reports exposes write_pdf."""

    def test_write_pdf_importable_from_package(self):
        from datascope.reports import write_pdf as fn
        assert callable(fn)


# ---------------------------------------------------------------------------
# Edge cases: metadata variations
# ---------------------------------------------------------------------------

class TestMetadataEdgeCases:
    """Report handles missing or unusual metadata gracefully."""

    def test_empty_metadata(self, tmp_path: Path):
        findings = process_findings([_critical_finding("col")])
        result = write_pdf(findings, {}, tmp_path / "no_meta.pdf")
        assert result.exists()

    def test_string_output_path(self, tmp_path: Path):
        """Passing output_path as a string (not Path) should still work."""
        str_path = str(tmp_path / "string_path.pdf")
        result = write_pdf([], _DEFAULT_METADATA, str_path)
        assert isinstance(result, Path)
        assert result.exists()
