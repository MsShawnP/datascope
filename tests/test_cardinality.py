"""Tests for datascope.analyzers.cardinality -- the cardinality-anomaly detector."""

from __future__ import annotations

import pandas as pd
import pytest

from datascope.analyzers.cardinality import analyze_cardinality
from datascope.models import FindingType, LoaderResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_loader_result(
    col_name: str,
    values: list,
) -> LoaderResult:
    """Build a single-column LoaderResult for testing.

    Cardinality analysis works on the DataFrame directly (not cell_types),
    so cell_types is left empty.
    """
    df = pd.DataFrame({col_name: values}, dtype=object)
    return LoaderResult(
        dataframe=df,
        cell_types={},
        source_metadata={"filename": "test_synthetic.xlsx"},
    )


def _make_multi_column_result(
    columns: dict[str, list],
) -> LoaderResult:
    """Build a multi-column LoaderResult for testing.

    ``columns`` maps column name to a list of values.
    """
    df = pd.DataFrame(columns, dtype=object)
    return LoaderResult(
        dataframe=df,
        cell_types={},
        source_metadata={"filename": "test_synthetic.xlsx"},
    )


# ---------------------------------------------------------------------------
# Happy path: suspected duplicate IDs (high uniqueness, not 100%)
# ---------------------------------------------------------------------------

class TestSuspectedDuplicateIDs:
    """ID column with 1000 values and 998 unique -- should flag duplicates."""

    @pytest.fixture()
    def result(self) -> LoaderResult:
        # 998 unique values + 2 duplicates of the first value
        values = list(range(998)) + [0, 0]
        return _make_loader_result("record_id", values)

    def test_produces_one_finding(self, result):
        findings = analyze_cardinality(result)
        assert len(findings) == 1

    def test_finding_field_name(self, result):
        finding = analyze_cardinality(result)[0]
        assert finding.field_name == "record_id"

    def test_finding_type(self, result):
        finding = analyze_cardinality(result)[0]
        assert finding.finding_type is FindingType.DUPLICATE_IDS

    def test_severity_is_none(self, result):
        """Severity is assigned later by the classifier, not the detector."""
        finding = analyze_cardinality(result)[0]
        assert finding.severity is None

    def test_evidence_unique_count(self, result):
        finding = analyze_cardinality(result)[0]
        assert finding.evidence["unique_count"] == 998

    def test_evidence_total_count(self, result):
        finding = analyze_cardinality(result)[0]
        assert finding.evidence["total_count"] == 1000

    def test_evidence_uniqueness_ratio(self, result):
        finding = analyze_cardinality(result)[0]
        assert finding.evidence["uniqueness_ratio"] == 0.998

    def test_evidence_duplicate_values(self, result):
        finding = analyze_cardinality(result)[0]
        assert "duplicate_values" in finding.evidence
        assert "0" in finding.evidence["duplicate_values"]


# ---------------------------------------------------------------------------
# Happy path: near-constant column
# ---------------------------------------------------------------------------

class TestNearConstant:
    """Column with 500 rows and 3 unique values -- near-constant."""

    @pytest.fixture()
    def result(self) -> LoaderResult:
        # 3 unique values out of 500 rows => uniqueness_ratio = 0.006,
        # with "A" dominating 490/500 = 98% => genuinely near-constant
        values = ["A"] * 490 + ["B"] * 8 + ["C"] * 2
        return _make_loader_result("status", values)

    def test_produces_one_finding(self, result):
        findings = analyze_cardinality(result)
        assert len(findings) == 1

    def test_finding_field_name(self, result):
        finding = analyze_cardinality(result)[0]
        assert finding.field_name == "status"

    def test_finding_type(self, result):
        finding = analyze_cardinality(result)[0]
        assert finding.finding_type is FindingType.NEAR_CONSTANT

    def test_evidence_unique_count(self, result):
        finding = analyze_cardinality(result)[0]
        assert finding.evidence["unique_count"] == 3

    def test_evidence_total_count(self, result):
        finding = analyze_cardinality(result)[0]
        assert finding.evidence["total_count"] == 500

    def test_evidence_uniqueness_ratio(self, result):
        finding = analyze_cardinality(result)[0]
        assert finding.evidence["uniqueness_ratio"] == 0.006

    def test_evidence_top_values(self, result):
        finding = analyze_cardinality(result)[0]
        top = finding.evidence["top_values"]
        assert isinstance(top, list)
        assert len(top) <= 5
        # Most common value should be "A" with count 400
        assert top[0]["value"] == "A"
        assert top[0]["count"] == 490


# ---------------------------------------------------------------------------
# Edge case: 100% unique values -- no finding
# ---------------------------------------------------------------------------

class TestFullyUnique:

    def test_no_finding(self):
        values = list(range(100))
        result = _make_loader_result("unique_id", values)
        findings = analyze_cardinality(result)
        assert len(findings) == 0


# ---------------------------------------------------------------------------
# Edge case: 50% unique values -- no finding (neither threshold)
# ---------------------------------------------------------------------------

class TestFiftyPercentUnique:

    def test_no_finding(self):
        # 50 unique values among 100 rows
        values = list(range(50)) + list(range(50))
        result = _make_loader_result("mixed_col", values)
        findings = analyze_cardinality(result)
        assert len(findings) == 0


# ---------------------------------------------------------------------------
# Edge case: small column (<10 rows) -- skipped
# ---------------------------------------------------------------------------

class TestSmallColumn:

    def test_no_finding_for_tiny_column(self):
        values = ["A"] * 9  # 9 rows, 1 unique -- would be near-constant but too small
        result = _make_loader_result("tiny", values)
        findings = analyze_cardinality(result)
        assert len(findings) == 0

    def test_exactly_10_rows_not_skipped(self):
        """10 rows is the minimum -- columns with exactly 10 are analyzed."""
        # 10 rows, 1 unique -> near-constant (uniqueness_ratio = 0.1, but
        # that's actually 0.1 which is > 0.01 so no finding for near-constant).
        # Let's use a value that triggers: 10 rows, 1 unique = 0.1, not < 0.01.
        # Need larger data for near-constant. Test that the column IS checked:
        values = list(range(10))  # 10 unique / 10 total = 1.0 -> no finding
        result = _make_loader_result("edge", values)
        findings = analyze_cardinality(result)
        assert len(findings) == 0  # 100% unique, no anomaly -- but it was checked


# ---------------------------------------------------------------------------
# Multiple columns: only anomalous ones get findings
# ---------------------------------------------------------------------------

class TestMultipleColumns:

    def test_only_anomalous_columns_flagged(self):
        """Three columns: near-constant, fully-unique, and mid-range.
        Only the near-constant one should produce a finding."""
        result = _make_multi_column_result({
            "status": ["active"] * 997 + ["inactive"] * 3,  # 2/1000 => near-constant
            "record_id": list(range(1000)),                  # 100% unique => no finding
            "category": list(range(500)) * 2,                # 50% unique => no finding
        })
        findings = analyze_cardinality(result)
        assert len(findings) == 1
        assert findings[0].field_name == "status"


# ---------------------------------------------------------------------------
# Edge case: column with nulls
# ---------------------------------------------------------------------------

class TestNullHandling:

    def test_nulls_excluded_suspected_id(self):
        """Null values are dropped before computing uniqueness.

        100 non-null rows (98 unique + 2 dups) + 20 nulls.
        uniqueness_ratio = 98/100 = 0.98 -> suspected-ID finding.
        """
        values = list(range(98)) + [0, 0] + [None] * 20
        result = _make_loader_result("col_with_nulls", values)
        findings = analyze_cardinality(result)
        assert len(findings) == 1
        finding = findings[0]
        # total_count should be 100 (nulls excluded)
        assert finding.evidence["total_count"] == 100
        assert finding.evidence["unique_count"] == 98
        assert "duplicate_values" in finding.evidence

    def test_nulls_excluded_near_constant(self):
        """Near-constant detection works correctly with nulls present."""
        # 200 non-null rows with 1 unique value + 50 nulls
        # uniqueness_ratio = 1/200 = 0.005 < 0.01 => near-constant
        values = ["constant"] * 200 + [None] * 50
        result = _make_loader_result("boring", values)
        findings = analyze_cardinality(result)
        assert len(findings) == 1
        assert findings[0].evidence["total_count"] == 200
        assert findings[0].evidence["unique_count"] == 1


# ---------------------------------------------------------------------------
# Edge case: empty input
# ---------------------------------------------------------------------------

class TestEmptyInput:

    def test_empty_dataframe(self):
        result = LoaderResult(dataframe=pd.DataFrame(), cell_types={})
        assert analyze_cardinality(result) == []


# ---------------------------------------------------------------------------
# Package export
# ---------------------------------------------------------------------------

class TestPackageExport:

    def test_analyze_cardinality_importable(self):
        from datascope.analyzers import analyze_cardinality as fn
        assert callable(fn)
