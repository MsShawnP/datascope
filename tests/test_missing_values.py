"""Tests for datascope.analyzers.missing_values -- the missing-value detector."""

from __future__ import annotations

import pandas as pd

from datascope.analyzers.missing_values import analyze_missing_values
from datascope.models import FindingType, LoaderResult


def _make_result(data: dict, cell_types: dict | None = None) -> LoaderResult:
    df = pd.DataFrame(data)
    return LoaderResult(
        dataframe=df,
        cell_types=cell_types or {},
        source_metadata={"filename": "test.csv", "row_count": len(df), "column_count": len(df.columns)},
    )


class TestBasicDetection:

    def test_column_above_threshold_produces_finding(self):
        data = {"a": [1, 2, None, None, None, 6, None, None, 9, 10]}
        result = _make_result(data)
        findings = analyze_missing_values(result, threshold_pct=10.0)
        assert len(findings) == 1
        assert findings[0].field_name == "a"
        assert findings[0].finding_type is FindingType.MISSING_VALUE_PATTERN

    def test_column_below_threshold_no_finding(self):
        data = {"a": [1, 2, 3, 4, 5, 6, 7, 8, 9, None]}
        result = _make_result(data)
        findings = analyze_missing_values(result, threshold_pct=15.0)
        assert len(findings) == 0

    def test_no_nulls_no_finding(self):
        data = {"a": [1, 2, 3], "b": ["x", "y", "z"]}
        result = _make_result(data)
        findings = analyze_missing_values(result)
        assert len(findings) == 0

    def test_empty_dataframe(self):
        result = _make_result({})
        findings = analyze_missing_values(result)
        assert len(findings) == 0

    def test_multiple_columns_with_nulls(self):
        data = {
            "a": [1, None, None, None, 5],
            "b": [None, None, None, None, None],
            "c": [1, 2, 3, 4, 5],
        }
        result = _make_result(data)
        findings = analyze_missing_values(result, threshold_pct=10.0)
        names = {f.field_name for f in findings}
        assert "a" in names
        assert "b" in names
        assert "c" not in names


class TestEvidence:

    def test_evidence_contains_expected_keys(self):
        data = {"a": [1, None, None, 4, 5]}
        result = _make_result(data)
        findings = analyze_missing_values(result, threshold_pct=10.0)
        ev = findings[0].evidence
        assert "null_count" in ev
        assert "total_rows" in ev
        assert "null_pct" in ev
        assert "distribution" in ev
        assert "sample_null_positions" in ev

    def test_null_pct_is_correct(self):
        data = {"a": [1, None, None, None, 5, 6, 7, 8, 9, 10]}
        result = _make_result(data)
        findings = analyze_missing_values(result, threshold_pct=10.0)
        assert findings[0].evidence["null_pct"] == 30.0
        assert findings[0].evidence["null_count"] == 3

    def test_sample_positions_limited(self):
        data = {"a": [None] * 20 + [1] * 5}
        result = _make_result(data)
        findings = analyze_missing_values(result, threshold_pct=10.0)
        assert len(findings[0].evidence["sample_null_positions"]) <= 5


class TestDistribution:

    def test_scattered_nulls(self):
        data = {"a": [None, 1, 2, None, 3, 4, None, 5, None, 6]}
        result = _make_result(data)
        findings = analyze_missing_values(result, threshold_pct=10.0)
        assert findings[0].evidence["distribution"] == "scattered"

    def test_contiguous_nulls(self):
        data = {"a": [1, 2, None, None, None, None, None, 8, 9, 10]}
        result = _make_result(data)
        findings = analyze_missing_values(result, threshold_pct=10.0)
        assert findings[0].evidence["distribution"] == "contiguous block"

    def test_nulls_at_end(self):
        values = list(range(20)) + [None] * 15
        data = {"a": values}
        result = _make_result(data)
        findings = analyze_missing_values(result, threshold_pct=10.0)
        assert findings[0].evidence["distribution"] == "concentrated at end"


class TestSeverityIntegration:

    def test_high_null_pct_gets_warning(self):
        from datascope.findings.severity import classify_severity
        from datascope.models import Severity

        finding = findings_with_pct(60.0)
        sev = classify_severity(finding)
        assert sev is Severity.WARNING

    def test_moderate_null_pct_gets_info(self):
        from datascope.findings.severity import classify_severity
        from datascope.models import Severity

        finding = findings_with_pct(25.0)
        sev = classify_severity(finding)
        assert sev is Severity.INFO


def findings_with_pct(pct: float):
    from datascope.models import Finding
    return Finding(
        field_name="test_col",
        finding_type=FindingType.MISSING_VALUE_PATTERN,
        evidence={"null_pct": pct, "null_count": 10, "total_rows": 100},
    )
